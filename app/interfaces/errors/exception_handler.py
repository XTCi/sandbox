import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.interfaces.errors.exceptions import APPException, NotFoundException, BadRequestException
from app.interfaces.schemas.base import Response

logger = logging.getLogger(__name__)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APPException)
    async def app_exception_handler(req: Request, e: APPException) -> JSONResponse:
        """处理沙箱系统的异常，统一响应"""
        logger.error(f"APPException:{e.msg}")
        return JSONResponse(
            status_code=e.status_code,
            content=Response(
                code=e.status_code,
                msg=e.msg,
                data={}
            ).model_dump()
        )
    @app.exception_handler(HTTPException)
    async def http_exception_handler(req: Request, e: HTTPException) -> JSONResponse:
        """处理fastapi的http抛出的异常"""
        logger.error(f"HttpException:{e.detail}")
        return JSONResponse(
            status_code=e.status_code,
            content=Response(
                code=e.status_code,
                msg=e.detail,
                data={}
            ).model_dump()
        )

    @app.exception_handler
    async def exception_handler(req: Request, e: Exception) -> JSONResponse:
        """处理未定义的异常"""
        logger.error(f"Exception: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=Response(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                msg="服务器出现异常请稍后尝试",
                data={}
            ).model_dump()
        )