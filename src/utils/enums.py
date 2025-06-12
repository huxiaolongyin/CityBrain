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
    DAMENG = "达梦数据库"
    POSTGRES = "PostgreSQL"
    KAFKA = "Kafka"
    HDFS = "HDFS"


class IndicatorType(str, Enum):
    HISTORY_TRACK = "历史轨迹检索"
    ROBOT_CHARGING = "机器人充电过程数据"
    ROBOT_USAGE = "机器人使用总时长"
    ENVIRONMENT = "环境监测数据"
