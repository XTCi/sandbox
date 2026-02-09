import logging
from typing import Any

from fastapi import status

logger = logging.getLogger(__name__)

class APPException(Exception):
    """异常基础类"""

    def __init__(self,
                 msg: str = "应用发生错误",
                 status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
                 data: Any = None) -> None:
        """构造函数"""
        self.msg = msg
        self.status_code = status_code
        self.data = data

        logger.error(f"沙箱发生错误：{msg} (code: {status_code})")
        super().__init__(self.msg)

class NotFoundException(APPException):
    """资源未找到异常"""

    def __init__(self, msg: str = "资源找不到，请核实后尝试") -> None:
        super().__init__(msg=msg, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestException(APPException):
    """错误请求异常"""
    def __init__(self, msg: str = "客户端请求错误，请检查后重试") -> None:
        super().__init__(msg=msg, status_code=status.HTTP_400_BAD_REQUEST)
