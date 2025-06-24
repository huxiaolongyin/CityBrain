from enum import Enum


class SyncType(str, Enum):
    STREAM = "实时"
    BATCH = "离线"


class Status(int, Enum):
    DISABLED = 0
    ENABLED = 1


class DataSourceType(str, Enum):
    MONGODB = "MongoDB"
    MYSQL = "MySQL"
    DM = "DM"
    POSTGRESQL = "PostgreSQL"
    KAFKA = "Kafka"
    HDFS = "HDFS"


class IndicatorType(str, Enum):
    HISTORY_TRACK = "历史轨迹数据"
    ROBOT_CHARGING = "机器人充电数据"
    ROBOT_USAGE = "机器人使用总时长"
    ROBOT_TASK = "机器人任务统计"
    ABNORMAL_DATA = "异常数据监控分析"
    ROBOT_EVENT = "机器人事件"
    ENVIRONMENT = "环境监测数据"
