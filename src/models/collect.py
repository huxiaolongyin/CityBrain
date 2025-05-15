from tortoise import fields

from utils.enums import Status

from .base import BaseModel, TimestampMixin


class Collect(BaseModel, TimestampMixin):
    """数据同步信息"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="数据同步任务")
    type = fields.CharField(max_length=50, description="数据同步类型")

    source = fields.ForeignKeyField(
        "app_system.Database", related_name="collect_sources", description="数据源ID"
    )
    source_table = fields.CharField(max_length=50, description="数据源表")

    target = fields.ForeignKeyField(
        "app_system.Database", related_name="collect_targets", description="目标ID"
    )
    target_table = fields.CharField(max_length=50, description="目标表")

    schedule = fields.CharField(max_length=50, description="调度周期", null=True)
    status = fields.IntEnumField(
        Status, default=Status.ENABLED, description="数据同步状态，1启用，0禁用"
    )

    class Meta:
        table = "collects"
        table_description = "数据同步信息"
