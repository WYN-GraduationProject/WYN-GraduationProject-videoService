import cv2
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse

from proto.video_service.video_model_pb2 import VideoFrame
from utils.model.video import VideoModel
from utils.tools.LoggingFormatter import LoggerManager
from utils.tools.gRPCManager import GrpcManager

router = APIRouter(
    prefix="/api/video",
    tags=["face"],
    responses={404: {"description": "Not found"}},
)

logger = LoggerManager(logger_name="face_api").get_logger()


def get_grpc_manager():
    """
    获取gRPC管理器
    :return: gRPC管理器
    """
    return GrpcManager()


async def process_video(video_model: VideoModel, grpc_manager) -> str | None:
    """
    处理视频
    :param video_model: 视频实体
    :param grpc_manager: gRPC管理器
    :return:
    """
    cap = cv2.VideoCapture(video_model.path + "/" + video_model.filename)
    video_model.fps = cap.get(cv2.CAP_PROP_FPS) > 100 and 30 or cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"视频帧率为: {video_model.fps}")
    if not cap.isOpened():
        logger.error(f"打开文件失败: {video_model.path + video_model.filename}")
        return

    async with grpc_manager.get_stub('face_detect_service') as stub:
        async def request_generator():
            """
            请求生成器
            :return: 视频处理的请求
            """
            while cap.isOpened():
                temp_ret, temp_frame = cap.read()
                if not temp_ret:
                    break
                _, img = cv2.imencode('.jpg', temp_frame)
                img_bytes = img.tobytes()
                yield VideoFrame(data=img_bytes, is_final=False, video_id=video_model.id)
            yield VideoFrame(is_final=True, fps=video_model.fps, video_id=video_model.id)

        try:
            logger.info("正在 RPC 调用预处理视频服务...")
            response_stream = stub.FaceDetection(request_generator())
            async for response in response_stream:
                video_model.data.append(response.data)
        except Exception as e:
            logger.error(f"RPC预处理视频失败: {e}")
        logger.info("视频流处理完成")
        video_model.path = "video_data/face_detection"
        await video_model.save()
        cap.release()
        return video_model.path + "/" + video_model.filename


@router.post("/face")
async def upload_video(video: UploadFile = File(...), grpc_manager: GrpcManager = Depends(get_grpc_manager)):
    # 传递视频文件路径给处理函数
    video_model = await VideoModel.http_video_save(video)
    file_name = await process_video(video_model, grpc_manager)
    return FileResponse(file_name, media_type="video/mp4", filename="video.mp4")
