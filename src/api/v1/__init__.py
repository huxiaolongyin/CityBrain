from fastapi import APIRouter

from .cluster import router as cluster_router
from .collect import router as collect_router
from .database import router as database_router
from .enums import router as enum_router
from .metric import router as metric_router

router = APIRouter()
router.include_router(enum_router, tags=["枚举管理"])
router.include_router(database_router, tags=["数据源管理"])
router.include_router(collect_router, tags=["数据同步管理"])
router.include_router(metric_router, tags=["指标管理"])
router.include_router(cluster_router, tags=["集群管理"])
