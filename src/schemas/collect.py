from typing import Optional, Union

from pydantic import BaseModel, Field

from models.database import Database
from utils.enums import Status


# 基础Collect模型
class CollectBase(BaseModel):
    name: str = Field(..., description="数据同步任务名称")
    type: str = Field(..., description="数据同步类型")
    source_id: int = Field(..., description="数据源ID", alias="sourceId")
    source_type: str = Field(..., description="数据源类型", alias="sourceType")
    source_name: str = Field(..., description="数据源名称", alias="sourceName")
    source_table: str = Field(..., description="数据源表", alias="sourceTable")
    target_id: int = Field(..., description="目标ID", alias="targetId")
    target_type: str = Field(..., description="目标类型", alias="targetType")
    target_name: str = Field(..., description="目标名称", alias="targetName")
    target_table: str = Field(..., description="目标表", alias="targetTable")
    schedule: Optional[str] = Field(None, description="调度周期")
    status: Optional[int] = Field(
        Status.ENABLED.value, description="数据同步状态，1启用，0禁用"
    )


# 创建Collect请求模型
class CollectCreate(CollectBase):
    """创建Collect请求模型"""

    ...


# 更新Collect请求模型
class CollectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="数据同步任务名称")
    type: Optional[str] = Field(None, description="数据同步类型")
    source_id: Optional[int] = Field(None, description="数据源ID", alias="sourceId")
    source_type: Optional[str] = Field(
        None, description="数据源类型", alias="sourceType"
    )
    source_name: Optional[str] = Field(
        None, description="数据源名称", alias="sourceName"
    )
    source_table: Optional[str] = Field(
        None, description="数据源表", alias="sourceTable"
    )
    target_id: Optional[int] = Field(None, description="目标ID", alias="targetId")
    target_type: Optional[str] = Field(None, description="目标类型", alias="targetType")
    target_name: Optional[str] = Field(None, description="目标名称", alias="targetName")
    target_table: Optional[str] = Field(None, description="目标表", alias="targetTable")
    schedule: Optional[str] = Field(None, description="调度周期")
    status: Optional[int] = Field(None, description="数据同步状态，1启用，0禁用")
