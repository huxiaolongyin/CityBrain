from datetime import date, datetime
from typing import Any, Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import Field

T = TypeVar("T")  # 用于泛型响应


class BaseResponse(JSONResponse):
    """基础响应模型"""

    def __init__(
        self,
        code: int = 200,
        success: bool = True,
        status_code: int = 200,
        msg: str = "成功",
        data: Any = None,
        **kwargs,
    ):

        if data:
            data = self.process_dates(data)
        content = {
            "code": code,
            "success": success,
            "msg": msg,
            "data": data,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=status_code)

    def process_dates(self, obj):
        """
        处理 data 字典中任意嵌套层级的日期类型数据
        """
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self.process_dates(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.process_dates(item) for item in obj]
        return obj


class Success(BaseResponse, Generic[T]):
    """成功响应模型，支持泛型数据"""

    ...


class Error(BaseResponse):
    """错误响应模型"""

    def __init__(
        self,
        code: int = 400,
        success: bool = False,
        msg: str = "服务器内部错误",
        data: Any = None,
        **kwargs,
    ):
        super().__init__(
            code=code, msg=msg, data=data, success=success, status_code=400, **kwargs
        )
