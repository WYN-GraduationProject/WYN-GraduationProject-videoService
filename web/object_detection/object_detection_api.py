import cv2
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse

from proto.video_service.video_model_pb2 import VideoFrame
from utils.model.video import VideoModel
from utils.tools.LoggingFormatter import LoggerManager
from utils.tools.gRPCManager import GrpcManager

router = APIRouter(
    prefix="/api/object_detection",
    tags=["object_detection"],
    responses={404: {"description": "Not found"}},
)

logger = LoggerManager(logger_name="object_detection_api").get_logger()


def get_grpc_manager():
    """
    获取gRPC管理器
    :return: gRPC管理器
    """
    return GrpcManager()


async def generate_video_frames(cap, video_model_id, fps):
    """
    生成视频帧
    :param cap: opencv视频对象
    :param video_model_id: 视频模型ID
    :param fps: 视频帧率
    """
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        _, img = cv2.imencode('.jpg', frame)
        img_bytes = img.tobytes()
        yield VideoFrame(data=img_bytes, is_final=False, video_id=video_model_id)
    yield VideoFrame(is_final=True, fps=fps, video_id=video_model_id)


async def process_video_with_grpc(video_model: VideoModel, grpc_manager, stub_name, update_path):
    """
    使用gRPC处理视频
    :param video_model: 视频模型
    :param grpc_manager: gRPC管理器
    :param stub_name: stub名称
    :param update_path: 更新路径
    :return: 处理后的视频路径
    """
    cap = cv2.VideoCapture(f"{video_model.path}/{video_model.filename}")
    video_model.fps = min(30, cap.get(cv2.CAP_PROP_FPS))  # Limit FPS to 30
    logger.info(f"Video FPS: {video_model.fps}")

    if not cap.isOpened():
        logger.error(f"打开文件失败: {video_model.path}/{video_model.filename}")
        return

    async with grpc_manager.get_stub(stub_name) as stub:
        try:
            logger.info(f"正在 RPC 调用 {stub_name} 服务...")
            if stub_name == 'video_pre_service':
                response_stream = stub.ProcessVideo(generate_video_frames(cap, video_model.id, video_model.fps))
            elif stub_name == 'object_detect_service':
                response_stream = stub.ObjectDetection(generate_video_frames(cap, video_model.id, video_model.fps))
            video_model.data = [response.data async for response in response_stream]
        except Exception as e:
            logger.error(f"RPC 调用失败: {e}")
        finally:
            cap.release()

    logger.info(f"{stub_name} 服务处理完成")
    video_model.path = update_path
    await video_model.save()
    return f"{video_model.path}/{video_model.filename}"


async def process_video(video_model: VideoModel, grpc_manager) -> str | None:
    """
    处理视频
    :param video_model: 视频模型
    :param grpc_manager: gRPC管理器
    :return: 处理后的视频路径
    """
    return await process_video_with_grpc(
        video_model, grpc_manager, 'object_detect_service', "video_data/object_detection"
    )


async def process_video_withpre(video_model: VideoModel, grpc_manager) -> str | None:
    """
    带有预处理的视频处理
    :param video_model: 视频模型
    :param grpc_manager: gRPC管理器
    :return: 处理后的视频路径
    """
    file_name = await process_video_with_grpc(
        video_model, grpc_manager, 'video_pre_service', "video_data/pre_process"
    )
    if file_name:
        return await process_video(video_model, grpc_manager)
    return file_name


@router.post("/test")
async def upload_video(video: UploadFile = File(...), grpc_manager: GrpcManager = Depends(get_grpc_manager)):
    video_model = await VideoModel.http_video_save(video)
    file_name = await process_video(video_model, grpc_manager)
    return FileResponse(file_name, media_type="video/mp4", filename="video.mp4")


@router.post("/withpre")
async def upload_video_with_pre(video: UploadFile = File(...), grpc_manager: GrpcManager = Depends(get_grpc_manager)):
    video_model = await VideoModel.http_video_save(video)
    file_name = await process_video_withpre(video_model, grpc_manager)
    return FileResponse(file_name, media_type="video/mp4", filename="video.mp4")
