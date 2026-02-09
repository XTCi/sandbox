from fastapi import APIRouter

from . import file, shell, supervisor

def create_api_router() -> APIRouter:
    """统一的API路由注册"""
    api_router = APIRouter()

    api_router.include_router(file.router)
    api_router.include_router(shell.router)
    api_router.include_router(supervisor.router)

    return api_router

router = create_api_router()
