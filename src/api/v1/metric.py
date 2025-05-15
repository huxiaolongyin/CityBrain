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
            data_item["longitude"] = random.uniform(120.0, 121.0)
            data_item["latitude"] = random.uniform(30.0, 31.0)
            data_item["speed"] = random.uniform(0, 120)
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

        elif indicator_type == IndicatorType.ENVIRONMENT:
            data_item["temperature"] = random.uniform(-10, 40)
            data_item["humidity"] = random.uniform(20, 90)
            data_item["airQuality"] = random.uniform(0, 500)
            data_item["noise"] = random.uniform(30, 90)
            data_item["light"] = random.uniform(0, 1000)

        sample_data.append(data_item)

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
            "status": {"type": "int", "description": "状态"},
            "timestamp": {"type": "datetime", "format": "%Y-%m-%d %H:%M:%S"},
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
