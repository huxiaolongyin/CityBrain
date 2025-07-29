from tortoise import fields

from .base import BaseModel, TimestampMixin


class Event(BaseModel, TimestampMixin):
    """事件模型"""

    id = fields.IntField(primary_key=True, description="事件ID")
    vin = fields.CharField(max_length=50, description="设备编号")
    event_type = fields.CharField(max_length=50, description="事件类型")
    event_time = fields.DatetimeField(description="事件发生时间")
    description = fields.CharField(max_length=255, null=True, description="事件描述")
    record_time = fields.DatetimeField(description="事件记录时间")

    class Meta:
        table = "events"
        table_description = "事件信息"


class Task(BaseModel, TimestampMixin):
    """任务模型"""

    id = fields.IntField(primary_key=True, description="任务ID")
    vin = fields.CharField(max_length=50, description="设备编号")
    task_type = fields.CharField(max_length=50, description="任务类型")
    status = fields.CharField(max_length=20, description="任务状态")
    task_start_time = fields.DatetimeField(description="任务执行时间")
    task_end_time = fields.DatetimeField(description="任务执行时间")
    task_usage_time = fields.FloatField(description="任务使用时间")

    class Meta:
        table = "tasks"
        table_description = "任务信息"
