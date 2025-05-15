from tortoise import fields

from utils.enums import Status

from .base import BaseModel, TimestampMixin


class Database(BaseModel, TimestampMixin):
    """数据库信息"""

    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=50, description="数据库名称")
    description = fields.CharField(max_length=255, description="数据库描述", null=True)
    type = fields.CharField(max_length=50, description="数据库类型")
    host = fields.CharField(max_length=50, description="数据库主机")
    port = fields.IntField(description="数据库端口")
    database = fields.CharField(max_length=255, description="选用的数据库")
    username = fields.CharField(max_length=50, description="数据库用户")
    password = fields.CharField(max_length=255, description="数据库密码")
    status = fields.IntEnumField(
        Status, default=Status.ENABLED, description="数据库状态，1启用，0禁用"
    )

    # update_by = fields.ForeignKeyField(
    #     "app_system.User", related_name="updated_databases", description="更新人"
    # )
    # create_by = fields.ForeignKeyField(
    #     "app_system.User", related_name="created_databases", description="创建人"
    # )

    class Meta:
        table = "databases"
        table_description = "数据库信息"
