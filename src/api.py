import json
import os
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from logger import get_logger
from pydantic import BaseModel

from task import TaskManager

logger = get_logger(__name__)


# API models
class TaskResponse(BaseModel):
    success: bool
    message: str
    task_name: str


class TaskStatusResponse(BaseModel):
    success: bool
    message: str
    task_name: str
    enabled: bool


class MetricsRequest(BaseModel):
    start_date: str
    end_date: str
    device_code: Optional[str] = None
    task_type: Optional[str] = None


class MetricsResponse(BaseModel):
    data: List[Dict[str, Any]]
    date_field: str
    value_field: str
    metric_name: str


class TaskType(str, Enum):
    SYNC = "sync"
    METRIC = "metric"


# 可以定义一个模型来表示维度结构
class DimensionFilter(BaseModel):
    field: str
    value: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动事件 - 使用单例模式获取 TaskManager
    global task_manager
    task_manager = TaskManager.get_instance()
    task_manager.start()
    logger.info("Task manager started via lifespan context")

    yield  # 应用运行中

    # 关闭事件
    if task_manager:
        task_manager.stop()
        logger.info("Task manager stopped via lifespan context")


# FastAPI Application
app = FastAPI(title="Dameng to Kafka Metrics Service")

# Task manager instance
task_manager = None


# Dependency to get task manager
def get_task_manager():
    global task_manager
    if task_manager is None:
        task_manager = TaskManager()
        task_manager.start()
    return task_manager


# 创建静态文件目录
os.makedirs("static", exist_ok=True)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def get_index():
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/tasks/{task_type}/{task_name}/start", response_model=TaskStatusResponse)
def start_task(
    task_type: TaskType,
    task_name: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    # 验证任务类型
    if task_type not in ["sync", "metric"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task type: {task_type}. Must be 'sync' or 'metric'",
        )

    # 验证任务存在
    task_exists = False
    if task_type == "sync":
        for task in task_manager.config.sync_tasks:
            if task["name"] == task_name:
                task_exists = True
                break
    else:  # metric
        for task in task_manager.config.metric_tasks:
            if task["name"] == task_name:
                task_exists = True
                break

    if not task_exists:
        raise HTTPException(
            status_code=404,
            detail=f"{task_type.capitalize()} task '{task_name}' not found",
        )

    # 启动任务
    success = task_manager.start_task(task_name)
    enabled = task_manager.task_state.is_task_enabled(task_name)

    return TaskStatusResponse(
        success=success,
        message=f"Task {task_name} {'started successfully' if success else 'is already running'}",
        task_name=task_name,
        enabled=enabled,
    )


@app.post("/tasks/{task_type}/{task_name}/stop", response_model=TaskStatusResponse)
def stop_task(
    task_type: TaskType,
    task_name: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    # 验证任务类型
    if task_type not in ["sync", "metric"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task type: {task_type}. Must be 'sync' or 'metric'",
        )

    # 验证任务存在
    task_exists = False
    if task_type == "sync":
        for task in task_manager.config.sync_tasks:
            if task["name"] == task_name:
                task_exists = True
                break
    else:  # metric
        for task in task_manager.config.metric_tasks:
            if task["name"] == task_name:
                task_exists = True
                break

    if not task_exists:
        raise HTTPException(
            status_code=404,
            detail=f"{task_type.capitalize()} task '{task_name}' not found",
        )

    # 停止任务
    success = task_manager.stop_task(task_name)
    enabled = task_manager.task_state.is_task_enabled(task_name)

    return TaskStatusResponse(
        success=success,
        message=f"Task {task_name} {'stopped successfully' if success else 'is already stopped'}",
        task_name=task_name,
        enabled=enabled,
    )


@app.get("/tasks/{task_type}/{task_name}/status", response_model=TaskStatusResponse)
def get_task_status(
    task_type: TaskType,
    task_name: str,
    task_manager: TaskManager = Depends(get_task_manager),
):
    # 验证任务类型
    if task_type not in ["sync", "metric"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task type: {task_type}. Must be 'sync' or 'metric'",
        )

    # 验证任务存在
    task_exists = False
    if task_type == "sync":
        for task in task_manager.config.sync_tasks:
            if task["name"] == task_name:
                task_exists = True
                break
    else:  # metric
        for task in task_manager.config.metric_tasks:
            if task["name"] == task_name:
                task_exists = True
                break

    if not task_exists:
        raise HTTPException(
            status_code=404,
            detail=f"{task_type.capitalize()} task '{task_name}' not found",
        )

    enabled = task_manager.task_state.is_task_enabled(task_name)

    return TaskStatusResponse(
        success=True,
        message=f"Task {task_name} is {'running' if enabled else 'stopped'}",
        task_name=task_name,
        enabled=enabled,
    )


@app.get("/metrics/{task_name}", response_model=MetricsResponse)
def get_metrics(
    task_name: str,
    start_date: str = Query(..., description="开始日期，ISO格式 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期，ISO格式 (YYYY-MM-DD)"),
    dimensions: Optional[str] = Query(
        None,
        description='维度过滤条件，JSON格式的列表，例如：[{"DEVICE_CODE",:"123"}]',
    ),
    metric: Optional[str] = Query(None, description="要查询的指标字段"),
    task_manager: TaskManager = Depends(get_task_manager),
):
    try:
        # 验证日期格式
        datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # 解析维度参数
        dimension_filters = []
        if dimensions:
            try:
                dimension_filters = json.loads(dimensions)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="维度参数不是有效的JSON格式"
                )

        # 获取任务配置
        metric_task_config = None
        for task in task_manager.config.metric_tasks:
            if task["name"] == task_name:
                metric_task_config = task
                break

        if not metric_task_config:
            raise HTTPException(
                status_code=404, detail=f"指标任务 '{task_name}' 不存在"
            )

        # 获取配置中的字段定义
        key_columns = list(metric_task_config.get("key_columns", {}).keys())
        # key_columns_with_desc = metric_task_config.get("key_columns", {})

        # 将timestamp_column从字典改为字符串
        timestamp_column_dict = metric_task_config.get("timestamp_column")
        timestamp_column = list(timestamp_column_dict.keys())[0].lower()

        if not timestamp_column:
            raise HTTPException(
                status_code=400, detail="timestamp_column 字段在配置中不存在"
            )

        # 获取值列名列表
        value_columns = list(metric_task_config.get("value_columns", {}).keys())
        # value_columns_with_desc = metric_task_config.get("value_columns", {})

        # 获取表名
        table_name = metric_task_config.get("table", "").lower()

        # 确定可用的指标字段 (value_columns 中不在 key_columns 中的字段)
        available_metrics = [
            col.lower() for col in value_columns if col not in key_columns
        ]
        # available_metrics_with_desc = {
        #     k.lower(): v
        #     for k, v in value_columns_with_desc.items()
        #     if k not in key_columns
        # }

        # 如果未指定指标，使用第一个可用指标
        if not metric and available_metrics:
            metric = available_metrics[0]
        elif metric and metric.upper() not in value_columns:
            raise HTTPException(
                status_code=400, detail=f"指定的指标 '{metric}' 不在可用指标列表中"
            )

        selected_fields = key_columns + [metric.lower()]
        # 获取指标数据
        metrics_data = task_manager.metric_db.query_metrics(
            table_name,
            start_date,
            end_date,
            dimension_filters,
            timestamp_column,
            selected_fields,
        )

        response = MetricsResponse(
            data=metrics_data,
            date_field=timestamp_column,
            value_field=metric.lower(),
            metric_name=task_name,
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取指标时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取指标时出错: {str(e)}")


@app.get("/tasks/sync", response_model=List[Dict[str, Any]])
def get_sync_tasks(task_manager: TaskManager = Depends(get_task_manager)):
    return task_manager.config.sync_tasks


@app.get("/tasks/metric", response_model=List[Dict[str, Any]])
def get_metric_tasks(task_manager: TaskManager = Depends(get_task_manager)):
    return task_manager.config.metric_tasks
