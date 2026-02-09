import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.interfaces.endpoints.routers import router
def setup_logging() -> None:
    """设置沙箱的日志"""
    # 获取配置
    setting = get_settings()
    # 获取根日志处理器
    root_logging = logging.getLogger()

    # 设置根日志处理器登记
    log_level = getattr(logging, setting.log_level)
    root_logging.setLevel(log_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )
    # 创建控制台日志输出处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # 6将控制台日志处理器添加到根日志处理器中
    root_logging.addHandler(console_handler)

    root_logging.info("沙箱系统日志模块初始化完成")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """fastapi的生命上下文周期管理器"""
    logger.info("沙箱正在初始化")

    try:
        yield
    finally:
        logger.info("沙箱关闭成功")

setup_logging()
logger = logging.getLogger(__name__)

openapi_tags= [
    {
        "name":"文件模块",
        "description": "文件的增删改查API接口"
    },
    {
        "name":"Shell模块",
        "description": "执行和查看ShellAPI接口"
    },
    {
        "name":"Supervisor模块",
        "description": "管理沙箱的进程，利用接口的方式"
    }

]
app = FastAPI(
    title="通用Agent沙箱系统",
    description="该沙箱中装了chrome、python、node，具备shell执行和文件操作",
    openapi_tags=openapi_tags,
    lifespan=lifespan,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
