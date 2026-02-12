import os
import re
from unittest import result
from fastapi import APIRouter, Depends

from app.interfaces.errors.exceptions import BadRequestException
from app.interfaces.schemas.base import Response
from app.interfaces.schemas.shell import ShellExecuteRequest, ShellKillRequest, ShellReadRequest, ShellWaitRequest, ShellWriteRequest
from app.interfaces.service_dependencies import get_shell_service
from app.models import shell
from app.services.shell import ShellService
from app.models.shell import ShellExecuteResult, ShellKillResult, ShellReadResult, ShellWaitResult, ShellWriteResult

router = APIRouter(prefix="/shell", tags=["shell模块"])


@router.post(
    path="/exec_shell",
    response_model=Response[ShellExecuteResult]
)
async def exec_command(
    request: ShellExecuteRequest,
    shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellExecuteResult]:
    """在给定的shell会话中运行指令"""
    # 判断session_id是否存在，不存在新建一个
    if not request.session_id or request.session_id == "":
        request.session_id = shell_service.create_session_id()
    # 判断运行的目录是否存在，不存在使用根目录
    if not request.exec_dir or request.exec_dir == "":
        request.exec_dir = os.path.expanduser("~")
    result = await shell_service.exec_command(
        session_id=request.session_id,
        exec_dir = request.exec_dir,
        command = request.command
    )

    return Response.success(data=result)



@router.post(
    path="/read-shell-output",
    response_model=Response[ShellReadResult]
)
async def read_shell_output(
    request: ShellReadRequest,
    shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellReadResult]:
    """根据传递的会话id+是否返回控制台表示获取shell执行的结果"""
    # 判断Shell会话是否存在
    if not request.session_id or request.session_id == "":
        raise BadRequestException("shell会话ID为空，请核实后重拾")
    # 调用服务获取命令执行结果
    result = await shell_service.read_shell_output(request.session_id, request.console)

    return Response.success(data=result)

@router.post(
    path="/wait-process",
    response_model=Response[ShellWaitResult]
)
async def wait_process(
    request: ShellWaitRequest,
    shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellWaitResult]:
    """根据会话id+超市时间获取shell结果"""
    # 判断sesionid是否存在
    if request.session_id or request.session_id == "":
        raise BadRequestException("Shell会话Id为空，请核实后重试")
    result = shell_service.wait_process(request.session_id,request.seconds)
    return Response.success(
        msg=f"进程结束，返回状态码(returncode):{result.returncode}",
        data=result
    )

@router.post(
    path="/write-shell-input",
    response_model=Response[ShellWriteResult]
)
async def write_shell_input(
    request: ShellWriteRequest,
    shell_service: ShellService = Depends(get_shell_service)
) -> Response[ShellWriteResult]:
    """根据会话加写入内容和按下回车标识向子进程写入数据"""
    # 判断shell会话是否存在
    if request.session_id or request.session_id == "":
        raise BadRequestException("Shell会话ID为空，请核实后重试")
    # 调研服务向子进程写入数据
    result = shell_service.write_shell_input(
        session_id=request.session_id,
        input_text=request.input_text,
        press_enter=request.press_enter
    )
    return Response.success(
        msg="向子进程写入数据成功",
        data=result
    )

@router.post(
    path="/kill-process",
    response_model=Response[ShellKillResult]
)
async def kill_process(
    request: ShellKillRequest,
    shell_service: ShellService = Depends(get_shell_service)) -> Response[ShellKillResult]:
    """根据传递的Shell会话id关闭指定会话"""

    # 判断会话是否存在
    if request.session_id or request.session_id == "":
        raise BadRequestException("shell会话ID为空，请核实后重试")
    result= shell_service.kill_process(request.session_id)
    return Response.success(
        msg="进程中指" if result.status == "terminated" else "进程已结束",
        data=result
    )