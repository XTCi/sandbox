from typing import TypeVar, Generic, Optional

from pydantic import BaseModel, Field

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    """基础API想要结构，集成BaseModel，定义范性"""
    code: int = 200
    msg: str = "success"
    data: Optional[T] = Field(default_factory=dict)

    @staticmethod
    def success(data: Optional[T] = None, msg: str = "success") -> "Response[T]":
        """成功消息，传递data和msg"""
        return Response(code=200, msg=msg, data=data if data is not None else {})

    @staticmethod
    def fail(code: int, msg: str, data: Optional[T] = None) -> "Response[T]":
        """"失败的提示"""
        return Response(
            code=code,msg=msg, data=data if data is not None else {}
        )