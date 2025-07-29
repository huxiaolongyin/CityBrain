import datetime
import os
import random
import tempfile
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from tortoise.expressions import Q

from api.v1.enums import IndicatorType
from models.metric import Event, Task
from schemas.common import Error
from schemas.metric import MetricExport
from utils.enums import ExportFormat

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
    if (
        indicator_type == IndicatorType.ROBOT_EVENT
        or indicator_type == IndicatorType.ROBOT_TASK
    ):
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        search: Q = Q()

        if vin:
            search: Q = search & Q(vin=vin)
        if indicator_type == IndicatorType.ROBOT_EVENT:
            search = search & Q(event_time__range=(start_date, end_date))
            query = Event.filter(search)
        elif indicator_type == IndicatorType.ROBOT_TASK:
            search = search & Q(task_start_time__range=(start_date, end_date))
            query = Task.filter(search)
        query = query.limit(page_size).offset((page - 1) * page_size)
        objs = await query.all()
        records = [await obj.to_dict() for obj in objs]
        total = await query.count()

    else:
        # 模拟数据
        records = []
        total = 20
        # 生成样例数据
        for i in range(total):
            data_item = {
                "id": 1000 + i,
                "vin": vin or f"VIN{random.randint(1000000, 9999999)}",
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

            elif indicator_type == IndicatorType.ENVIRONMENT:
                data_item["temperature"] = random.uniform(-10, 40)
                data_item["humidity"] = random.uniform(20, 90)
                data_item["airQuality"] = random.uniform(0, 500)
                data_item["noise"] = random.uniform(30, 90)
                data_item["light"] = random.uniform(0, 1000)

            records.append(data_item)

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
            "vin": {"type": "string", "description": "设备编号"},
            "taskType": {"type": "string", "description": "任务类型"},
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
            "duration": {"type": "int", "description": "持续时间(秒)"},
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
            "vin": {"type": "string", "description": "设备编号"},
            "eventType": {"type": "string", "description": "事件类型"},
            "eventTime": {"type": "string", "description": "事件发生时间"},
            "description": {"type": "string", "description": "事件描述"},
            "recordTime": {
                "type": "datetime",
                "format": "%Y-%m-%d %H:%M:%S",
                "description": "记录时间",
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
            "records": records,
            "columns": columns,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    }


@router.post("/metrics/export", summary="导出指标数据")
async def export_indicator_data(export_data: MetricExport):
    """
    导出指标数据，支持CSV和Excel格式
    """

    # 调用现有的查询函数获取数据
    result = await query_indicator_data(
        start_date=export_data.start_date,
        end_date=export_data.end_date,
        vin=export_data.vin,
        indicator_type=export_data.indicator_type,
        page=1,
        page_size=export_data.limit,
    )

    # 提取数据和列信息
    records = result["data"]["records"]
    columns = result["data"]["columns"]

    # 创建列标题映射
    column_labels = {
        col_name: col_info["description"] for col_name, col_info in columns.items()
    }

    # 创建DataFrame并重命名列
    df = pd.DataFrame(records)
    df = df.rename(columns=column_labels)

    # 生成文件名
    base_filename = f"{export_data.indicator_type.value}_{export_data.start_date}_{export_data.end_date}"

    # 创建临时目录用于存储导出文件
    temp_dir = Path(tempfile.gettempdir()) / "citybrain_exports"
    os.makedirs(temp_dir, exist_ok=True)

    if export_data.export_format == ExportFormat.CSV:
        # 创建CSV文件
        file_path = temp_dir / f"{base_filename}.csv"
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

        # 直接返回文件
        return FileResponse(
            path=file_path,
            filename=f"{base_filename}.csv",
            media_type="text/csv",
            background=BackgroundTask(lambda: os.remove(file_path)),
        )

    elif export_data.export_format == ExportFormat.EXCEL:
        # 创建Excel文件
        file_path = temp_dir / f"{base_filename}.xlsx"

        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            df.to_excel(
                writer, sheet_name=export_data.indicator_type.value, index=False
            )

            # 获取xlsxwriter对象进行格式设置
            workbook = writer.book
            worksheet = writer.sheets[export_data.indicator_type.value]

            # 设置标题格式
            header_format = workbook.add_format(
                {
                    "bold": True,
                    "text_wrap": True,
                    "valign": "top",
                    "bg_color": "#D9E1F2",
                    "border": 1,
                }
            )

            # 应用格式并调整列宽
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                max_len = max(df[value].astype(str).map(len).max(), len(value)) + 2
                worksheet.set_column(col_num, col_num, min(max_len, 30))  # 最大宽度30

        return FileResponse(
            path=file_path,
            filename=f"{base_filename}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            background=BackgroundTask(lambda: os.remove(file_path)),
        )

    # 如果代码执行到这里，说明导出格式不支持
    return Error(msg=f"不支持的导出格式: {export_data.export_format}")
