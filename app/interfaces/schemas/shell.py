from typing import Optional

from pydantic import BaseModel, Field

class ShellExecuteRequest(BaseModel):
    """执行shell的请求体"""
    session_id: Optional[str] = Field(default=None,description="会话的唯一标识符")
    exec_dir: Optional[str] = Field(default=None, description="执行命令的工作目录")
    command: str = Field(..., description="shell命令")

class ShellReadRequest(BaseModel):
    """查看Shell执行内容请求结构体"""
    session_id: str = Field(..., description="目标Shell会话多唯一标识富符")
    console: Optional[bool] = Field(default=None, description="是否返回控制台记录列表")

class ShellWaitRequest(BaseModel):
    session_id: str = Field(...,description="shell会话id")
    seconds: Optional[int] = Field(default=None, description="等待时机，单位为s")

class ShellWriteRequest(BaseModel):
    """Shell写入请求结构体"""
    session_id: str = Field(..., description="目标Shell会话唯一标识符")
    input_text: str = Field(..., description="需要写入的内容文本")
    press_enter: bool = Field(default=True, description="是否按下回车键")

class ShellKillRequest(BaseModel):
    """关闭会话请求结构体"""
    session_id: str = Field(..., description="会话id")