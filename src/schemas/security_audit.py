from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityAuditCreate(BaseModel):
    """安全审计创建请求"""

    query_indicator: str = Field(
        ..., description="查询指标类型", alias="queryIndicator"
    )
    query_user: str = Field(..., description="查询人", alias="queryUser")
    query_reason: str = Field(..., description="查询理由", alias="queryReason")


class SecurityAuditUpdate(SecurityAuditCreate):
    """安全审计更新请求"""

    ...
