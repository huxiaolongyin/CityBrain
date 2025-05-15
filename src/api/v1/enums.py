from fastapi import APIRouter, Query

from utils.enums import DataSourceType, IndicatorType, Status, SyncType

router = APIRouter()


# 添加获取枚举值的API端点
@router.get("/enums", summary="获取所有枚举值选项")
async def get_enum_options(type: str = Query(None, description="枚举类型")):
    """
    获取系统中所有枚举值选项，用于前端生成选择框
    """
    records = {
        "syncTypes": [{"value": item.value, "key": item.name} for item in SyncType],
        "statusOptions": [
            {
                "value": item.value,
                "key": item.name,
                "label": "启用" if item.value == 1 else "禁用",
            }
            for item in Status
        ],
        "dataSourceTypes": [
            {"value": item.value, "key": item.name} for item in DataSourceType
        ],
        "indicatorTypes": [
            {"value": item.value, "key": item.name} for item in IndicatorType
        ],
    }
    if type:
        records = records[type]
    return {
        "code": 200,
        "success": True,
        "msg": "获取枚举值成功",
        "data": {
            "records": records,
            "type": ["syncTypes", "statusOptions", "dataSourceTypes", "indicatorTypes"],
        },
    }
