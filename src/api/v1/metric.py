import datetime
import random

from fastapi import APIRouter, Query

from api.v1.enums import IndicatorType

router = APIRouter()


# ============= 大数据查询接口 =============
@router.get("/metrics", summary="查询指标数据")
async def query_indicator_data(
    start_date: str = Query(
        ...,
        description="开始日期 (YYYY-MM-DD)",
        alias="startDate",
    ),
    end_date: str = Query(
        ...,
        description="结束日期 (YYYY-MM-DD)",
        alias="endDate",
    ),
    vin: str = Query(None, description="车辆VIN码"),
    indicator_type: IndicatorType = Query(
        ...,
        description="指标类型",
        alias="indicatorType",
    ),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量", alias="pageSize"),
):
    """
    查询指标数据，支持按日期范围、VIN和指标类型筛选
    """
    # 模拟数据
    sample_data = []

    # 生成样例数据
    for i in range(20):
        data_item = {
            "id": 1000 + i,
            "vin": vin or f"VIN{random.randint(10000, 99999)}",
            "createTime": (
                datetime.datetime.strptime(start_date, "%Y-%m-%d")
                + datetime.timedelta(
                    days=random.randint(
                        0,
                        (
                            datetime.datetime.strptime(end_date, "%Y-%m-%d")
                            - datetime.datetime.strptime(start_date, "%Y-%m-%d")
                        ).days,
                    )
                )
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 根据指标类型生成不同的动态字段
        if indicator_type == IndicatorType.HISTORY_TRACK:
            data_item["longitude"] = random.uniform(118.28, 120.0)
            data_item["latitude"] = random.uniform(25.25, 26.65)
            data_item["speed"] = random.uniform(0, 35)
            data_item["direction"] = random.randint(0, 359)
            data_item["status"] = random.choice(["行驶中", "停车", "怠速"])
            data_item["timestamp"] = data_item["createTime"]

        elif indicator_type == IndicatorType.ROBOT_CHARGING:
            data_item["batteryLevel"] = random.uniform(10, 100)
            data_item["chargingPower"] = random.uniform(1, 10)
            data_item["temperature"] = random.uniform(25, 45)
            data_item["chargingTime"] = random.randint(10, 120)
            data_item["chargingVoltage"] = random.uniform(220, 240)
            data_item["chargingCurrent"] = random.uniform(10, 30)
            data_item["voltage"] = random.uniform(220, 240)
            data_item["current"] = random.uniform(10, 30)

        elif indicator_type == IndicatorType.ROBOT_USAGE:
            data_item["totalHours"] = random.uniform(100, 5000)
            data_item["activeHours"] = random.uniform(50, 3000)
            data_item["idleHours"] = random.uniform(10, 1000)
            data_item["powerCycles"] = random.randint(10, 500)
            data_item["lastActivated"] = (
                (
                    datetime.datetime.now()
                    - datetime.timedelta(days=random.randint(1, 30))
                ).strftime("%Y-%m-%d %H:%M:%S"),
            )

        elif indicator_type == IndicatorType.ROBOT_TASK:
            data_item["taskId"] = f"TASK{random.randint(1000, 9999)}"
            data_item["taskName"] = random.choice(
                ["清洁任务", "巡检任务", "配送任务", "维护任务"]
            )
            data_item["taskStatus"] = random.choice(
                ["进行中", "已完成", "已暂停", "已取消", "待执行"]
            )
            data_item["startTime"] = (
                datetime.datetime.strptime(data_item["createTime"], "%Y-%m-%d %H:%M:%S")
                - datetime.timedelta(hours=random.randint(1, 24))
            ).strftime("%Y-%m-%d %H:%M:%S")
            data_item["endTime"] = (
                datetime.datetime.strptime(data_item["createTime"], "%Y-%m-%d %H:%M:%S")
                + datetime.timedelta(hours=random.randint(1, 12))
            ).strftime("%Y-%m-%d %H:%M:%S")
            data_item["duration"] = random.randint(30, 480)  # 分钟
            data_item["completionRate"] = random.uniform(0, 100)
            data_item["priority"] = random.choice(["高", "中", "低"])

        elif indicator_type == IndicatorType.ABNORMAL_DATA:
            data_item["anomalyType"] = random.choice(
                ["温度异常", "电池异常", "传感器异常", "通信异常", "运行异常"]
            )
            data_item["severity"] = random.choice(["严重", "警告", "提示"])
            data_item["description"] = random.choice(
                [
                    "设备温度超过正常范围",
                    "电池电量异常下降",
                    "传感器数据异常",
                    "网络连接不稳定",
                    "运行速度异常",
                ]
            )
            data_item["detectedTime"] = data_item["createTime"]
            data_item["resolvedTime"] = (
                (
                    datetime.datetime.strptime(
                        data_item["createTime"], "%Y-%m-%d %H:%M:%S"
                    )
                    + datetime.timedelta(hours=random.randint(1, 48))
                ).strftime("%Y-%m-%d %H:%M:%S")
                if random.choice([True, False])
                else None
            )
            data_item["isResolved"] = data_item["resolvedTime"] is not None
            data_item["alertCount"] = random.randint(1, 10)

        elif indicator_type == IndicatorType.ROBOT_EVENT:
            data_item["eventType"] = random.choice(
                [
                    "启动",
                    "停止",
                    "充电开始",
                    "充电结束",
                    "任务开始",
                    "任务完成",
                    "故障",
                    "维护",
                ]
            )
            data_item["eventCode"] = f"EVT{random.randint(1000, 9999)}"
            data_item["eventDescription"] = random.choice(
                [
                    "机器人正常启动",
                    "机器人停止运行",
                    "开始充电",
                    "充电完成",
                    "开始执行任务",
                    "任务执行完成",
                    "检测到故障",
                    "进入维护模式",
                ]
            )
            data_item["eventTime"] = data_item["createTime"]
            data_item["location"] = random.choice(
                ["A区", "B区", "C区", "充电站", "维护区"]
            )
            data_item["operator"] = random.choice(["系统", "管理员", "技术员", "自动"])
            data_item["relatedTaskId"] = (
                f"TASK{random.randint(1000, 9999)}"
                if random.choice([True, False])
                else None
            )

        elif indicator_type == IndicatorType.ENVIRONMENT:
            data_item["temperature"] = random.uniform(-10, 40)
            data_item["humidity"] = random.uniform(20, 90)
            data_item["airQuality"] = random.uniform(0, 500)
            data_item["noise"] = random.uniform(30, 90)
            data_item["light"] = random.uniform(0, 1000)

        sample_data.append(data_item)

    # 定义列结构
    if indicator_type == IndicatorType.HISTORY_TRACK:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "longitude": {"type": "float", "description": "经度"},
            "latitude": {"type": "float", "description": "纬度"},
            "speed": {"type": "float", "description": "速度"},
            "direction": {"type": "float", "description": "方向"},
            "status": {"type": "string", "description": "状态"},
            "timestamp": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "时间戳",
            },
        }
    elif indicator_type == IndicatorType.ROBOT_CHARGING:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "batteryLevel": {"type": "float", "description": "电池电量百分比"},
            "chargingPower": {"type": "float", "description": "充电功率"},
            "temperature": {"type": "float", "description": "温度"},
            "chargingTime": {"type": "int", "description": "充电时间"},
            "chargingVoltage": {"type": "float", "description": "充电电压"},
            "chargingCurrent": {"type": "float", "description": "充电电流"},
            "voltage": {"type": "float", "description": "电压"},
            "current": {"type": "float", "description": "电流"},
        }
    elif indicator_type == IndicatorType.ROBOT_USAGE:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "totalHours": {"type": "float", "description": "总使用时间"},
            "activeHours": {"type": "float", "description": "活跃时间"},
            "idleHours": {"type": "float", "description": "空闲时间"},
            "powerCycles": {"type": "int", "description": "充电次数"},
            "lastActivated": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "最近激活时间",
            },
        }
    elif indicator_type == IndicatorType.ROBOT_TASK:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "taskId": {"type": "string", "description": "任务ID"},
            "taskName": {"type": "string", "description": "任务名称"},
            "taskStatus": {"type": "string", "description": "任务状态"},
            "startTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "开始时间",
            },
            "endTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "结束时间",
            },
            "duration": {"type": "int", "description": "持续时间(分钟)"},
            "completionRate": {"type": "float", "description": "完成率"},
            "priority": {"type": "string", "description": "优先级"},
        }
    elif indicator_type == IndicatorType.ABNORMAL_DATA:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "anomalyType": {"type": "string", "description": "异常类型"},
            "severity": {"type": "string", "description": "严重程度"},
            "description": {"type": "string", "description": "异常描述"},
            "detectedTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "检测时间",
            },
            "resolvedTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "解决时间",
            },
            "isResolved": {"type": "boolean", "description": "是否已解决"},
            "alertCount": {"type": "int", "description": "告警次数"},
        }
    elif indicator_type == IndicatorType.ROBOT_EVENT:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "eventType": {"type": "string", "description": "事件类型"},
            "eventCode": {"type": "string", "description": "事件代码"},
            "eventDescription": {"type": "string", "description": "事件描述"},
            "eventTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "事件时间",
            },
            "location": {"type": "string", "description": "位置"},
            "operator": {"type": "string", "description": "操作者"},
            "relatedTaskId": {"type": "string", "description": "关联任务ID"},
        }
    elif indicator_type == IndicatorType.ENVIRONMENT:
        columns = {
            "createTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "创建时间",
            },
            "vin": {"type": "string", "description": "识别码"},
            "temperature": {"type": "float", "description": "温度"},
            "humidity": {"type": "float", "description": "湿度"},
            "airQuality": {"type": "float", "description": "空气质量"},
            "noise": {"type": "float", "description": "噪音"},
            "light": {"type": "float", "description": "光照强度"},
        }

    return {
        "code": 200,
        "success": True,
        "msg": "查询指标数据成功",
        "data": {
            "records": sample_data,
            "columns": columns,
            "total": len(sample_data),
            "page": page,
            "pageSize": page_size,
        },
    }
