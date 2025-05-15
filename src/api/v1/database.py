from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from tortoise.expressions import Q

from schemas.common import Error, Success
from schemas.database import DatabaseCreate, DatabaseUpdate
from services import DatabaseService, database_service
from utils.enums import Status

router = APIRouter()


def get_db_service() -> DatabaseService:
    return database_service


@router.get("/databases", summary="获取数据源")
async def get_database_list(
    type_or_name: Optional[str] = Query(
        None, description="数据源类型或名称", alias="typeOrName"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        10, ge=1, le=100, description="每页数量(1-100)", alias="pageSize"
    ),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    获取所有数据源，支持按类型或名称筛选，并提供分页功能
    """
    q = Q()
    if type_or_name:
        q &= Q(type=type_or_name) | Q(name__icontains=type_or_name)

    total, database_list = await db_service.get_list(
        page, page_size, q, exclude=["password"]
    )

    return Success(
        msg="获取数据列表成功",
        data={
            "records": database_list,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    )


@router.get("/databases/{id}", summary="获取数据源详情")
async def get_database_detail(
    id: int = Path(..., description="数据源ID"),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    获取指定ID的数据源详情，包括关联的数据表信息
    """
    try:
        database_obj = await db_service.get(id)
    except ValueError as e:
        return Error(msg=str(e))

    records = await database_obj.to_dict(exclude_fields=["password"])

    # TODO: 这里可以添加获取关联表信息的逻辑，现在使用模拟数据
    records["tables"] = [
        {"id": 1, "name": "device_status", "description": "设备状态数据表"},
        {"id": 2, "name": "device_metrics", "description": "设备性能指标表"},
        {"id": 3, "name": "device_alerts", "description": "设备告警记录表"},
        {"id": 4, "name": "device_maintenance", "description": "设备维护记录表"},
        {"id": 5, "name": "device_inventory", "description": "设备资产清单表"},
    ]

    return Success(
        msg="获取数据源详情成功",
        data={"records": records},
    )


@router.post("/databases", summary="创建数据源")
async def create_database(
    database: DatabaseCreate,
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    创建新的数据源
    """
    try:
        result = await db_service.create(
            database, unique_field="name", unique_field_error_message="数据源名称已存在"
        )
    except ValueError as e:
        return Error(msg=str(e))

    return Success(msg="创建数据源成功", data={"id": result.id})


@router.put("/databases/{id}", summary="更新数据源")
async def update_database(
    database: DatabaseUpdate,
    id: int = Path(..., description="数据源ID"),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    更新指定ID的数据源信息
    """
    try:
        database_obj = await db_service.update(id, database)
    except ValueError as e:
        return Error(msg=str(e))

    return Success(
        msg="更新数据源成功",
        data={"id": database_obj.id},
    )


@router.delete("/databases/{id}", summary="删除数据源")
async def delete_database(
    id: int = Path(..., description="数据源ID"),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    删除指定ID的数据源
    """
    try:
        await db_service.delete(id)
        return Success(msg="删除数据源成功", data={"id": id})
    except ValueError as e:
        return Error(msg=str(e))
    except Exception as e:
        return Error(msg=str(e))


@router.post(
    "/databases/{id}/test-connection",
    summary="测试数据库连接",
)
async def test_database_connection(
    id: int = Path(..., description="数据源ID"),
    db_service: DatabaseService = Depends(get_db_service),
):
    """
    测试指定ID的数据源连接是否可用
    """
    result = await db_service.test_connection(id)

    return {
        "code": 200,
        "success": result["status"],
        "msg": result["message"],
        "data": None,
    }


# @router.post(
#     "/databases/{id}/toggle-status",
#     summary="切换数据源状态",
# )
# async def toggle_database_status(
#     id: int = Path(..., description="数据源ID"),
#     db_service: DatabaseService = Depends(get_db_service),
# ):
#     """
#     切换数据源的启用/禁用状态
#     """
#     pass
