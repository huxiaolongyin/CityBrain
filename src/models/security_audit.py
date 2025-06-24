from tortoise import fields

from .base import BaseModel, TimestampMixin


class SecurityAudit(BaseModel, TimestampMixin):
    """安全审计记录"""

    id = fields.IntField(primary_key=True)
    query_indicator = fields.CharField(max_length=100, description="查询指标类型")
    query_user = fields.CharField(max_length=50, description="查询人")
    query_reason = fields.TextField(description="查询理由")

    # 审计信息
    ip_address = fields.CharField(max_length=45, description="访问IP地址", null=True)
    user_agent = fields.CharField(max_length=500, description="用户代理", null=True)
    request_method = fields.CharField(max_length=10, description="请求方法", null=True)
    request_url = fields.CharField(max_length=500, description="请求URL", null=True)

    class Meta:
        table = "security_audits"
        table_description = "安全审计记录"
