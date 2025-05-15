from typing import Optional

from pydantic import BaseModel, Field

from utils.enums import Status


# 请求和响应模型
class DatabaseBase(BaseModel):
    name: str = Field(..., description="数据库名称")
    description: Optional[str] = Field(None, description="数据库描述")
    type: str = Field(..., description="数据库类型")
    host: str = Field(..., description="数据库主机")
    port: int = Field(..., description="数据库端口")
    database: str = Field(..., description="选用的数据库")
    username: str = Field(..., description="数据库用户")
    password: str = Field(..., description="数据库密码")


class DatabaseCreate(DatabaseBase):
    status: Optional[int] = Field(
        Status.ENABLED.value, description="数据库状态。1:启用，0:禁用"
    )


class DatabaseUpdate(BaseModel):
    name: Optional[str] = Field(None, description="数据库名称")
    description: Optional[str] = Field(None, description="数据库描述")
    type: Optional[str] = Field(None, description="数据库类型")
    host: Optional[str] = Field(None, description="数据库主机")
    port: Optional[int] = Field(None, description="数据库端口")
    database: Optional[str] = Field(None, description="选用的数据库")
    username: Optional[str] = Field(None, description="数据库用户")
    password: Optional[str] = Field(None, description="数据库密码")
    status: Optional[int] = Field(None, description="数据库状态，1启用，0禁用")
