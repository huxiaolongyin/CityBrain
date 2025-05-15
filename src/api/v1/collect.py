import datetime
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from tortoise.expressions import Q

from api.v1.enums import DataSourceType, Status, SyncType
from schemas.collect import CollectCreate, CollectUpdate
from schemas.common import Error, Success
from services import CollectService, collect_service

router = APIRouter()


# ============= 数据模型定义 =============
class CollectTask(BaseModel):
    id: int
    name: str
    type: SyncType
    sourceId: int
    sourceType: DataSourceType
    sourceName: str
    sourceTable: str
    targetId: int
    targetType: DataSourceType
    targetName: str
    targetTable: str
    schedule: str
    status: Status
    createTime: str
    updateTime: str


class CreateCollectTask(BaseModel):
    name: str
    type: SyncType
    sourceId: int
    sourceType: DataSourceType
    sourceName: str = ""
    sourceTable: str
    targetId: int
    targetType: DataSourceType
    targetName: str = ""
    targetTable: str
    schedule: str
    status: Status = Status.ENABLED


class UpdateCollectTask(BaseModel):
    name: Optional[str] = None
    type: Optional[SyncType] = None
    sourceId: Optional[int] = None
    sourceType: Optional[DataSourceType] = None
    sourceName: Optional[str] = None
    sourceTable: Optional[str] = None
    targetId: Optional[int] = None
    targetType: Optional[DataSourceType] = None
    targetName: Optional[str] = None
    targetTable: Optional[str] = None
    schedule: Optional[str] = None
    status: Optional[Status] = None


class IndicatorData(BaseModel):
    id: int
    vin: str
    createTime: str
    data: Dict[str, Any]


class ClusterStatus(BaseModel):
    totalDevices: int
    activeCores: int
    totalCores: int
    totalMemory: str
    availableMemory: str
    totalStorage: str
    usedStorage: str
    usagePercent: float
    services: List[Dict[str, Any]]


def get_collect_service():
    return collect_service


# ============= 数据采集接口 =============
@router.get("/collects", summary="获取数据同步任务列表")
async def get_collect_list(
    type: SyncType = Query(None, description="数据同步类型(实时/离线)"),
    source_type: List[DataSourceType] = Query(
        None, description="数据来源类型", alias="sourceType"
    ),
    target_type: List[DataSourceType] = Query(
        None, description="数据去向类型", alias="targetType"
    ),
    status: Status = Query(None, description="状态(1:启用,0:禁用)"),
    name: str = Query(None, description="任务名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, description="每页数量", alias="pageSize"),
    collect_service: CollectService = Depends(get_collect_service),
):
    """
    获取所有数据采集任务，支持按同步类型、数据去向类型、状态和名称筛选
    """
    q = Q()
    if type:
        q &= Q(type=type)
    if source_type:
        q &= Q(source__type__in=source_type)
    if target_type:
        q &= Q(target__type__in=target_type)
    if status:
        q &= Q(status=status)
    if name:
        q &= Q(name__icontains=name)

    total, collect_list = await collect_service.get_list(
        page, page_size, q, prefetch=["source", "target"]
    )

    return Success(
        msg="获取数据源详情成功",
        data={
            "records": collect_list,
            "total": total,
            "page": page,
            "pageSize": page_size,
        },
    )


@router.post("/collects", summary="创建数据同步任务")
async def create_collect_task(
    collect: CollectCreate,
    collect_service: CollectService = Depends(get_collect_service),
):
    """
    创建新的数据同步任务
    """
    try:
        collect_obj = await collect_service.create(collect)
    except ValueError as e:
        return Error(msg=str(e))

    return Success(msg="创建数据同步任务成功", data={"id": collect_obj.id})


@router.get("/collects/{id}", summary="获取单个数据同步任务详情")
async def get_collect_task(
    id: int = Path(..., description="任务ID"),
    collect_service: CollectService = Depends(get_collect_service),
):
    """
    根据ID获取数据同步任务详情
    """
    # 模拟从数据库获取任务
    try:
        collect_obj = await collect_service.get(id=id)
    except ValueError as e:
        return Error(msg=str(e))

    await collect_obj.fetch_related("source", "target")
    result = await collect_obj.to_dict()
    result["sourceType"] = collect_obj.source.type
    result["sourceName"] = collect_obj.source.name
    result["targetType"] = collect_obj.target.type
    result["targetName"] = collect_obj.target.name

    return Success(msg="获取数据同步任务成功", data=result)


@router.put("/collects/{id}", summary="更新数据同步任务")
async def update_collect_task(
    id: int = Path(..., description="任务ID"),
    collect: CollectUpdate = Body(..., description="需要更新的任务信息"),
    collect_service: CollectService = Depends(get_collect_service),
):
    """
    更新数据同步任务信息
    """
    try:
        collect_obj = await collect_service.update(id, collect)
    except ValueError as e:
        return Error(msg=str(e))

    return Success(msg="更新数据同步任务成功", data={"id": collect_obj.id})


@router.delete("/collects/{id}", summary="删除数据同步任务")
async def delete_collect_task(
    id: int = Path(..., description="任务ID"),
    collect_service: CollectService = Depends(get_collect_service),
):
    """
    删除数据同步任务
    """
    try:
        await collect_service.delete(id)
    except ValueError as e:
        return Error(msg=str(e))

    return Success(msg="删除数据同步任务成功", data={"id": id})
