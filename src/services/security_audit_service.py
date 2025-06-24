from typing import List, Optional

from tortoise.expressions import Q

from models.security_audit import SecurityAudit
from schemas.security_audit import SecurityAuditCreate, SecurityAuditUpdate

from .crud import CRUD


class SecurityAuditsService(
    CRUD[SecurityAudit, SecurityAuditCreate, SecurityAuditUpdate]
):
    def __init__(self):
        """初始化安全审计服务，使用SecurityAudit模型"""
        super().__init__(SecurityAudit)

    async def get_list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: Optional[List[str]] = None,
        prefetch: Optional[List[str]] = None,
        exclude: list = None,
    ):
        """
        获取所有安全审计信息
        """
        total, objs = await super().get_list(
            page=page,
            page_size=page_size,
            search=search,
            order=order,
            prefetch=prefetch,
        )

        return total, [await obj.to_dict(exclude_fields=exclude) for obj in objs]
