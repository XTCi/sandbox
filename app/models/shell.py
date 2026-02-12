import asyncio
from sys import ps1
from tkinter import N, NO
from token import OP
from click import command
from pydantic import BaseModel, Field, ConfigDict

from typing import Optional, List


class ShellExecuteResult(BaseModel):
    """shell命令执行结果"""
    session_id: str = Field(..., description="shell会话ID")
    command: str = Field(..., description="shell执行的命令")
    status: str = Field(..., description="执行状态")
    returncode: Optional[int] = Field(default=None, description="进程返回的代码，进程结束返回")
    output: Optional[str] = Field(default=None, description="进程执行结束后的结果，执行完后才有值")

class ConsoleRecord(BaseModel):
    """Shell命令控制台记录"""
    ps1: str = Field(..., description="ps1")
    command: str = Field(..., description="执行的命令")
    output: str = Field(default="", description="输出内容")
class Shell(BaseModel):
    """会话模型"""
    process: asyncio.subprocess.Process = Field(..., description="会话中的子进程")
    exec_dir: str = Field(..., description="会话执行目录")
    output: str = Field(..., description="会话输出")
    console_records: List[ConsoleRecord] = Field(default_factory=list, description="Shell会话中控制记录列表")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class ShellWaitResult(BaseModel):
    """会话等待结果模型"""
    returncode: int = Field(..., description="子进程返回的代码")

class ShellReadResult(BaseModel):
    """shell命令结果模型"""
    session_id: str = Field(..., description="Shell会话ID")
    output: str = Field(..., description="Shell会话输出内容")
    console_records: List[ConsoleRecord] = Field(default_factory=list, description="控制台记录")


class ShellWriteResult(BaseModel):
    status: str = Field(..., description="写入状态")

class ShellKillResult(BaseModel):
    """Shell命令关闭结果"""
    status: str = Field(..., description="进程状体啊")
    returncode: int = Field(..., description="进程返回状态吗")