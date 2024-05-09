import asyncio
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from utils.tools.LoggingFormatter import LoggerManager
from utils.tools.NacosManager import NacosManager, NacosServerUtils
from web.admin import admin_api
from web.face import face_api
from web.object_detection import object_detection_api


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    global nacos_serverutils
    nacos_manager = NacosManager()
    nacos_serverutils = nacos_manager.get_server_utils("video-service", "0.0.0.0", 8003)
    await nacos_serverutils.register_service()
    asyncio.create_task(nacos_serverutils.beat(10))
    try:
        yield
    finally:
        await nacos_serverutils.deregister_service()


app = FastAPI(lifespan=app_lifespan)

app.include_router(face_api.router)
app.include_router(object_detection_api.router)
app.include_router(admin_api.router)

logger = LoggerManager(logger_name="video_service").get_logger()
nacos_logger = logging.getLogger('nacos.client')
nacos_logger.setLevel(logging.WARNING)
nacos_serverutils: NacosServerUtils = None  # 定义变量以便在事件处理器中引用

if __name__ == "__main__":
    logger.info("服务启动...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
