import asyncio
import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from tortoise.expressions import Q

from models.collect import Collect
from models.database import Database
from schemas.collect import CollectCreate, CollectUpdate
from utils.enums import Status
from utils.logger import get_logger

from .crud import CRUD

logger = get_logger(__name__)

# 数据同步任务的JSON配置文件路径
DATAX_JOBS_PATH = os.environ.get("DATAX_JOBS_PATH", "data/datax/jobs")

# Airflow DAGs 文件路径
AIRFLOW_DAGS_PATH = os.environ.get("AIRFLOW_DAGS_PATH", "data/airflow/dags")

# 模板文件路径
TEMPLATES_PATH = os.environ.get("TEMPLATES_PATH", "templates")

# 创建 Jinja2 环境
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_PATH),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# 数据库连接器映射
DATABASE_READER_MAP = {
    "Mongodb": "mongodbreader",
    "MySQL": "mysqlreader",
    "PostgreSQL": "postgresqlreader",
    "Oracle": "oraclereader",
    "SQLServer": "sqlserverreader",
    "Dameng": "rdbmsreader",
}
DATABASE_WRITER_MAP = {
    "Mongodb": "mongodbwriter",
    "MySQL": "mysqlwriter",
    "PostgreSQL": "postgresqlwriter",
    "Oracle": "oraclewriter",
    "SQLServer": "sqlserverwriter",
    "Dameng": "rdbmswriter",
}


class CollectService(CRUD[Collect, CollectCreate, CollectUpdate]):
    """
    数据同步服务类，提供数据同步任务管理的业务逻辑
    """

    def __init__(self):
        """初始化数据同步服务，使用Collect模型"""
        super().__init__(Collect)

    async def _get_connection_details(self, database_id: int) -> Dict[str, Any]:
        """获取数据库连接详细信息"""
        database_data = await Database.get(id=database_id)

        return {
            "jdbcUrl": f"jdbc:{database_data.type.lower()}://{database_data.host}:{database_data.port}/{database_data.database}",
            "username": database_data.username,
            "password": database_data.password,
            "type": database_data.type,
            "database": database_data.database,
        }

    async def _generate_datax_job_json(
        self, collect_data: CollectCreate, collect_id: int
    ) -> str:
        """
        生成DataX JSON配置文件
        Args:
            collect_data: 数据同步任务的创建数据
            collect_id: 数据同步任务的ID
        :return: DataX JSON配置文件的路径
        """
        try:
            # 假设你有一个函数可以根据 source_id 和 target_id 获取详细的连接信息
            source_conn_details = await self._get_connection_details(
                collect_data.source_id
            )
            target_conn_details = await self._get_connection_details(
                collect_data.target_id
            )

            # 准备模板变量
            template_vars = {
                # 读取器配置
                "reader_name": DATABASE_READER_MAP.get(collect_data.source_type),
                "source_username": source_conn_details.get("username"),
                "source_password": source_conn_details.get("password"),
                "source_jdbc_url": source_conn_details.get("jdbcUrl"),
                "source_database": source_conn_details.get("database"),
                "source_table": collect_data.source_table,
                "source_columns": ["*"],  # 或者从 collect_data 获取特定列
                # 写入器配置
                "writer_name": DATABASE_WRITER_MAP.get(collect_data.target_type),
                "target_username": target_conn_details.get("username"),
                "target_password": target_conn_details.get("password"),
                "target_jdbc_url": target_conn_details.get("jdbcUrl"),
                "target_database": target_conn_details.get("database"),
                "target_table": collect_data.target_table,
                "target_columns": ["*"],  # 确保与reader端列对应
                # 预处理SQL
                # "pre_sql": [f"DELETE FROM {collect_data.target_table} WHERE 1=1"],
                # 可选参数
                "channel": 1,
                "error_limit_record": 0,
                "error_percentage": 0.02,
            }

            # 如果是增量同步，添加 where 条件
            if collect_data.inc_or_full == "inc":
                if collect_data.inc_column_type == "int":
                    template_vars["source_where"] = (
                        f"{collect_data.inc_column} > '${{last_watermark}}'"
                    )

                elif collect_data.inc_column_type == "datetime" or "date":
                    template_vars["source_where"] = (
                        f"{collect_data.inc_column} > '${{last_watermark}}' AND {collect_data.inc_column} <= '${{current_processing_time}}'"
                    )
                else:
                    raise ValueError("不支持的增量字段类型")

            # 加载模板
            template = jinja_env.get_template("datax_job_template.json.j2")

            # 渲染模板
            rendered_template = template.render(**template_vars)

            # 生成文件名，确保唯一性
            job_filename = f"collect_{collect_id}_{collect_data.source_type.lower()}_{collect_data.target_type.lower()}.json"
            job_filepath = os.path.join(DATAX_JOBS_PATH, job_filename)

            # 创建目录并写入文件
            os.makedirs(DATAX_JOBS_PATH, exist_ok=True)
            with open(job_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_template)

            logger.info(f"DataX JSON配置文件已生成: {job_filepath}")
            return job_filepath  # 返回生成的文件路径

        except Exception as e:
            logger.error(f"生成DataX JSON配置文件失败: {e}")
            raise e

    async def _generate_airflow_dag_py(
        self, collect_data: CollectCreate, collect_id: int, datax_job_json_path: str
    ):
        """
        生成Airflow DAG的Python脚本
        Args:
            collect_data: 数据同步任务的创建数据
            collect_id: 数据同步任务的ID
            datax_job_json_path: DataX JSON配置文件的路径
        Returns:
            Airflow DAG的Python脚本的路径
        """
        try:
            dag_id = f"dag_task_{collect_id}_{collect_data.source_type.lower()}_{collect_data.target_type.lower()}"
            datax_job_filename = os.path.basename(datax_job_json_path)

            # 判断是否需要增量同步
            incremental_sync = (
                hasattr(collect_data, "inc_or_full")
                and collect_data.inc_or_full == "inc"
            )

            # 准备模板变量
            template_vars = {
                "dag_id": dag_id,
                "description": f"从{collect_data.source_type}同步数据到{collect_data.target_type}",
                "schedule": collect_data.schedule,
                "tags": [
                    "datax",
                    "sync",
                    collect_data.source_type,
                    collect_data.target_type,
                ],
                "datax_job_filename": datax_job_filename,
                "docker_network": "citybrain_city_brain_net",
                "datax_image": "huas/datax",
                "collect_id": collect_id,
                "incremental_sync": incremental_sync,
            }

            # 如果是增量同步，添加额外的变量
            if incremental_sync:
                # 获取元数据数据库连接信息
                # 这些应该从环境变量或配置文件中获取
                template_vars.update(
                    {
                        "meta_db_host": os.environ.get("META_DB_HOST", "postgres"),
                        "meta_db_port": os.environ.get("META_DB_PORT", "5432"),
                        "meta_db_name": os.environ.get("META_DB_NAME", "city_brain"),
                        "meta_db_user": os.environ.get("META_DB_USER", "admin"),
                        "meta_db_password": os.environ.get(
                            "META_DB_PASSWORD", "12345HTW"
                        ),
                        "datax_job_template_path": datax_job_json_path,
                    }
                )
            # 加载模板
            template = jinja_env.get_template("airflow_dag_template.py.j2")

            # 渲染模板
            rendered_template = template.render(**template_vars)

            # 生成文件名和路径
            dag_filename = f"{dag_id}.py"
            dag_filepath = os.path.join(AIRFLOW_DAGS_PATH, dag_filename)

            # 创建目录并写入文件
            os.makedirs(AIRFLOW_DAGS_PATH, exist_ok=True)
            with open(dag_filepath, "w", encoding="utf-8") as f:
                f.write(rendered_template)
            logger.info(f"DataX DAG文件已生成: {dag_filepath}")
            return dag_filepath

        except Exception as e:
            logger.error(f"生成DataX DAG文件失败: {e}")
            return None

    async def get_list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: Optional[List[str]] = None,
        prefetch: Optional[List[str]] = None,
        exclude: list = None,
    ):
        """
        获取所有数据同步任务
        """
        total, objs = await super().get_list(
            page=page,
            page_size=page_size,
            search=search,
            order=order,
            prefetch=prefetch,
        )
        result = []
        for obj in objs:
            item = await obj.to_dict(exclude_fields=exclude)
            source_database = await Database.get_or_none(id=obj.source_id)
            target_database = await Database.get_or_none(id=obj.target_id)
            item["sourceName"] = source_database.name
            item["targetName"] = target_database.name
            item["sourceType"] = source_database.type
            item["targetType"] = target_database.type
            result.append(item)

        return total, result

    async def create(self, obj_in: CollectCreate, exclude=None):
        """
        创建新的数据同步任务

        Args:
            obj_in: 包含创建数据的对象
            exclude: 排除的字段

        Returns:
            创建的Collect实例

        Raises:
            ValueError: 当任务名已存在或来源/目标数据库不存在时
        """
        try:
            # 检查任务名是否已存在
            if await Collect.filter(name=obj_in.name).first():
                raise ValueError("数据同步任务名称已存在")

            # 验证源数据库是否存在
            source_db = await Database.get_or_none(id=obj_in.source_id)
            if not source_db:
                raise ValueError(f"数据源ID {obj_in.source_id} 不存在")

            # 验证目标数据库是否存在
            target_db = await Database.get_or_none(id=obj_in.target_id)
            if not target_db:
                raise ValueError(f"目标数据库ID {obj_in.target_id} 不存在")

            # 增量同步时，写入默认水印值
            if obj_in.inc_or_full == "inc":
                if obj_in.inc_column_type == "datetime":
                    obj_in.last_watermark = "1970-01-01 08:00:00"
                elif obj_in.inc_column_type == "int":
                    obj_in.last_watermark = 0
                elif obj_in.inc_column_type == "date":
                    obj_in.last_watermark = "1970-01-01"
                else:
                    raise ValueError("不支持的增量字段类型")

            # 创建同步任务
            collect = await super().create(
                obj_in,
                exclude=[
                    "source_name",
                    "source_type",
                    "target_name",
                    "target_type",
                ],
            )
            # 生成配置文件
            datax_path = await self._generate_datax_job_json(obj_in, collect.id)
            await self._generate_airflow_dag_py(obj_in, collect.id, datax_path)

            # # 如果状态为启用，自动启动任务
            # if collect.status == Status.ENABLED:
            #     logger.info(f"新创建的同步任务 {collect.id} 状态为启用，自动启动任务")
            #     start_result = await self.start_collect_job(collect.id)
            #     if not start_result.get("status"):
            #         logger.warning(
            #             f"自动启动任务 {collect.id} 失败: {start_result.get('message')}"
            #         )
            #         # 注意：这里我们选择继续而不是失败，因为任务已创建成功，只是自动启动失败

            # 创建同步任务
            return collect

        except Exception as e:
            raise e

    async def update(
        self, id: int, obj_in: Union[CollectUpdate, Dict[str, Any]], exclude=None
    ):
        """
        更新数据同步任务

        Args:
            id: 同步任务ID
            obj_in: 包含更新数据的对象或字典
            exclude: 排除的字段

        Returns:
            更新后的Collect实例

        Raises:
            ValueError: 当同步任务不存在或来源/目标数据库不存在时
        """
        # 获取原始任务数据，用于后续比较
        original_collect = await super().get(id=id)
        if not original_collect:
            raise ValueError(f"数据同步任务ID {id} 不存在")

        # 将obj_in转换为字典
        update_data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        # 如果更新了源数据库ID，验证它是否存在
        if "source_id" in update_data and update_data["source_id"] is not None:
            source_db = await Database.get_or_none(id=update_data["source_id"])
            if not source_db:
                raise ValueError(f"数据源ID {update_data['source_id']} 不存在")
            # 更新数据源类型
            update_data["source_type"] = source_db.type

        # 如果更新了目标数据库ID，验证它是否存在
        if "target_id" in update_data and update_data["target_id"] is not None:
            target_db = await Database.get_or_none(id=update_data["target_id"])
            if not target_db:
                raise ValueError(f"目标数据库ID {update_data['target_id']} 不存在")
            # 更新目标类型
            update_data["target_type"] = target_db.type

        # 如果是增量同步并更新了增量列类型，设置默认水印值
        if (
            update_data.get("inc_or_full") == "inc"
            and "inc_column_type" in update_data
            and (
                original_collect.inc_or_full != "inc"
                or original_collect.inc_column_type != update_data["inc_column_type"]
            )
        ):
            if update_data["inc_column_type"] == "datetime":
                update_data["last_watermark"] = "1970-01-01 08:00:00"
            elif update_data["inc_column_type"] == "int":
                update_data["last_watermark"] = 0
            elif update_data["inc_column_type"] == "date":
                update_data["last_watermark"] = "1970-01-01"
            else:
                raise ValueError("不支持的增量字段类型")

        # 记录原始状态，用于判断是否需要启动/停止任务
        original_status = original_collect.status
        # 获取更新后的状态（如果存在更新）
        new_status = update_data.get("status", original_status)

        # 更新同步任务
        updated_collect = await super().update(id, update_data, exclude)

        # 检查是否需要重新生成配置文件
        need_regenerate = False
        critical_fields = [
            "source_id",
            "target_id",
            "source_table",
            "target_table",
            "inc_or_full",
            "inc_column",
            "inc_column_type",
            "schedule",
        ]

        for field in critical_fields:
            if field in update_data:
                need_regenerate = True
                break

        # 如果关键字段有变化，重新生成配置文件
        if need_regenerate:
            # 获取完整的更新后任务对象
            collect_data = (
                await Collect.filter(id=id).prefetch_related("source", "target").first()
            )
            if not collect_data:
                raise ValueError(f"数据同步任务ID {id} 不存在")

            # 转换为 CollectCreate 对象以便重用现有方法
            collect_create_data = CollectCreate(
                name=collect_data.name,
                type=collect_data.type,
                sourceId=collect_data.source_id,
                targetId=collect_data.target_id,
                sourceType=collect_data.source.type,
                sourceName=collect_data.source.name,
                targetType=collect_data.target.type,
                targetName=collect_data.target.name,
                sourceTable=collect_data.source_table,
                targetTable=collect_data.target_table,
                schedule=collect_data.schedule,
                incOrFull=collect_data.inc_or_full,
                incColumn=collect_data.inc_column,
                incColumnType=collect_data.inc_column_type,
                lastWatermark=collect_data.last_watermark,
                status=collect_data.status,
            )

            try:
                # 删除旧的配置文件
                await self._remove_old_config_files(
                    id, collect_data.source.type, collect_data.target.type
                )

                # 生成新的配置文件
                datax_path = await self._generate_datax_job_json(
                    collect_create_data, id
                )
                await self._generate_airflow_dag_py(collect_create_data, id, datax_path)

                logger.info(f"已重新生成ID为 {id} 的数据同步任务配置文件")
            except Exception as e:
                logger.error(f"重新生成配置文件失败: {e}")
                # 这里可以选择是否抛出异常或者只记录错误
                # 如果配置文件生成失败但数据库已更新，可能需要回滚或通知用户

        # 根据状态变化自动启停任务
        # if original_status != new_status:
        #     if new_status == Status.ENABLED:
        #         # 状态从禁用变为启用，自动启动任务
        #         logger.info(f"同步任务 {id} 状态变更为启用，自动启动任务")
        #         start_result = await self.start_collect_job(id)
        #         if not start_result.get("status"):
        #             logger.warning(
        #                 f"自动启动任务 {id} 失败: {start_result.get('message')}"
        #             )

        #     elif new_status == Status.DISABLED:
        #         # 状态从启用变为禁用，自动停止任务
        #         logger.info(f"同步任务 {id} 状态变更为禁用，自动停止任务")
        #         stop_result = await self.stop_collect_job(id)
        #         if not stop_result.get("status"):
        #             logger.warning(
        #                 f"自动停止任务 {id} 失败: {stop_result.get('message')}"
        #             )

        # 如果配置变更且任务仍处于启用状态，考虑重启任务
        # elif new_status == Status.ENABLED and need_regenerate:
        #     logger.info(f"同步任务 {id} 配置已更新且状态为启用，尝试重启任务")
        #     # 先停止正在运行的任务
        #     await self.stop_collect_job(id)
        #     # 等待一段时间确保任务完全停止
        #     await asyncio.sleep(2)
        #     # 重新启动任务
        #     start_result = await self.start_collect_job(id)
        #     if not start_result.get("status"):
        #         logger.warning(f"重启任务 {id} 失败: {start_result.get('message')}")

        return updated_collect

    async def _remove_old_config_files(
        self, collect_id: int, source_type: str, target_type: str
    ):
        """
        删除旧的配置文件
        Args:
            collect_id: 数据同步任务ID
            source_type: 源数据库类型
            target_type: 目标数据库类型
        """
        try:
            # 删除旧的DataX配置文件
            datax_pattern = (
                f"collect_{collect_id}_{source_type.lower()}_{target_type.lower()}.json"
            )
            datax_path = os.path.join(DATAX_JOBS_PATH, datax_pattern)
            if os.path.exists(datax_path):
                os.remove(datax_path)
                logger.info(f"已删除旧的DataX配置文件: {datax_path}")

            # 删除旧的Airflow DAG文件
            dag_pattern = (
                f"dag_task_{collect_id}_{source_type.lower()}_{target_type.lower()}.py"
            )
            dag_path = os.path.join(AIRFLOW_DAGS_PATH, dag_pattern)
            if os.path.exists(dag_path):
                os.remove(dag_path)
                logger.info(f"已删除旧的Airflow DAG文件: {dag_path}")
        except Exception as e:
            logger.error(f"删除旧配置文件失败: {e}")
            # 可以选择忽略这个错误，因为它不会阻止新文件的创建

    # async def get_by_status(
    #     self, status: Status, skip: int = 0, limit: int = 100
    # ) -> List[Collect]:
    #     """
    #     获取指定状态的数据同步任务

    #     Args:
    #         status: 状态枚举值
    #         skip: 跳过记录数
    #         limit: 返回记录数限制

    #     Returns:
    #         满足条件的Collect列表
    #     """
    #     return await self.get_multi(skip=skip, limit=limit, status=status)

    # async def get_by_database(
    #     self, database_id: int, skip: int = 0, limit: int = 100
    # ) -> List[Collect]:
    #     """
    #     获取与指定数据库相关的所有同步任务（作为源或目标）

    #     Args:
    #         database_id: 数据库ID
    #         skip: 跳过记录数
    #         limit: 返回记录数限制

    #     Returns:
    #         与该数据库相关的Collect列表
    #     """
    #     queryset = Collect.filter(sourceId=database_id) | Collect.filter(
    #         targetId=database_id
    #     )
    #     return await queryset.offset(skip).limit(limit).all()

    async def start_collect_job(self, id: int) -> Dict[str, Any]:
        """
        启动数据同步任务

        Args:
            id: 同步任务ID

        Returns:
            包含状态和消息的字典
        """
        # 获取同步任务信息
        collect = await self.get(id)
        if not collect:
            return {"status": False, "message": "数据同步任务不存在"}

        if collect.status != Status.ENABLED:
            return {"status": False, "message": "数据同步任务未启用，无法执行"}

        # 获取数据库类型信息
        source_db = await Database.get(id=collect.source_id)
        target_db = await Database.get(id=collect.target_id)

        # 构建DAG ID
        dag_id = f"dag_task_{id}_{source_db.type.lower()}_{target_db.type.lower()}"

        # Airflow API配置
        airflow_host = os.environ.get("AIRFLOW_HOST", "http://localhost:8082")
        airflow_user = os.environ.get("AIRFLOW_USER", "admin")
        airflow_password = os.environ.get("AIRFLOW_PASSWORD", "airflow_1398")

        # 等待DAG被Airflow加载（DAG文件可能刚刚创建）
        # 注意：实际生产环境可能需要更复杂的逻辑或不同的等待策略
        await self._wait_for_dag_to_be_loaded(
            airflow_host, airflow_user, airflow_password, dag_id
        )

        try:
            # 使用httpx库调用Airflow API
            async with httpx.AsyncClient() as client:
                # 设置基本认证
                auth = (airflow_user, airflow_password)

                # 触发DAG运行
                trigger_url = f"{airflow_host}/api/v2/dags/{quote(dag_id)}/dagRuns"

                response = await client.post(
                    trigger_url,
                    auth=auth,
                    json={"conf": {}},  # 可以在这里传递配置参数
                    timeout=30.0,  # 设置超时时间
                )

                if response.status_code in (200, 201):
                    return {
                        "status": True,
                        "message": f"数据同步任务已提交执行，DAG ID: {dag_id}",
                        "dag_id": dag_id,
                        "run_id": response.json().get("dag_run_id"),
                    }
                else:
                    logger.error(
                        f"启动任务失败: {response.status_code} - {response.text}"
                    )
                    return {
                        "status": False,
                        "message": f"启动失败: Airflow API返回错误 {response.status_code}",
                    }

        except Exception as e:
            logger.error(f"启动数据同步任务失败: {str(e)}")
            return {"status": False, "message": f"启动失败: {str(e)}"}

    async def _wait_for_dag_to_be_loaded(
        airflow_host: str,
        airflow_user: str,
        airflow_password: str,
        dag_id: str,
        max_attempts: int = 10,
        interval: int = 3,
    ):
        """
        等待DAG文件被Airflow加载

        Args:
            airflow_host: Airflow服务器地址
            airflow_user: Airflow用户名
            airflow_password: Airflow密码
            dag_id: DAG ID
            max_attempts: 最大尝试次数
            interval: 每次尝试的间隔时间(秒)

        Returns:
            True表示DAG已加载，False表示超时
        """
        async with httpx.AsyncClient() as client:
            auth = (airflow_user, airflow_password)

            for attempt in range(max_attempts):
                try:
                    # 检查DAG是否存在
                    dag_url = f"{airflow_host}/api/v2/dags/{quote(dag_id)}"
                    response = await client.get(dag_url, auth=auth, timeout=10.0)

                    if response.status_code == 200:
                        dag_info = response.json()
                        # 检查DAG是否已暂停
                        if dag_info.get("is_paused", True):
                            # 如果DAG被暂停，尝试取消暂停
                            await client.patch(
                                dag_url,
                                auth=auth,
                                json={"is_paused": False},
                                timeout=10.0,
                            )
                            logger.info(f"DAG {dag_id} 已取消暂停")

                        logger.info(f"DAG {dag_id} 已加载")
                        return True

                    logger.info(
                        f"DAG {dag_id} 尚未加载，等待中... (尝试 {attempt+1}/{max_attempts})"
                    )
                    await asyncio.sleep(interval)

                except Exception as e:
                    logger.warning(f"检查DAG状态时出错: {str(e)}，等待重试...")
                    await asyncio.sleep(interval)

            logger.warning(f"等待DAG {dag_id} 加载超时")
            return False

    async def stop_collect_job(self, id: int) -> Dict[str, Any]:
        """
        停止数据同步任务的所有正在运行的实例

        Args:
            id: 同步任务ID

        Returns:
            包含状态和消息的字典
        """
        # 获取同步任务信息
        collect = await self.get(id)
        if not collect:
            return {"status": False, "message": "数据同步任务不存在"}

        # 获取数据库类型信息
        source_db = await Database.get(id=collect.source_id)
        target_db = await Database.get(id=collect.target_id)

        # 构建DAG ID
        dag_id = f"dag_task_{id}_{source_db.type.lower()}_{target_db.type.lower()}"

        # Airflow API配置
        airflow_host = os.environ.get("AIRFLOW_HOST", "http://localhost:8082")
        airflow_user = os.environ.get("AIRFLOW_USER", "admin")
        airflow_password = os.environ.get("AIRFLOW_PASSWORD", "airflow_1398")

        try:
            # 使用httpx库调用Airflow API
            async with httpx.AsyncClient() as client:
                # 设置基本认证
                auth = (airflow_user, airflow_password)

                # 获取正在运行的DAG实例
                dag_runs_url = (
                    f"{airflow_host}/api/v2/dags/{quote(dag_id)}/dagRuns?state=running"
                )
                response = await client.get(dag_runs_url, auth=auth, timeout=10.0)

                if response.status_code != 200:
                    return {
                        "status": False,
                        "message": f"获取运行中的任务失败: Airflow API返回错误 {response.status_code}",
                    }

                dag_runs = response.json().get("dag_runs", [])
                if not dag_runs:
                    return {"status": True, "message": "没有正在运行的任务实例"}

                # 停止所有运行中的实例
                stopped_count = 0
                for dag_run in dag_runs:
                    dag_run_id = dag_run.get("dag_run_id")
                    if not dag_run_id:
                        continue

                    # 调用API终止DAG运行
                    terminate_url = f"{airflow_host}/api/v2/dags/{quote(dag_id)}/dagRuns/{quote(dag_run_id)}/setFailed"
                    terminate_response = await client.post(
                        terminate_url, auth=auth, timeout=10.0
                    )

                    if terminate_response.status_code in (200, 204):
                        stopped_count += 1
                    else:
                        logger.error(
                            f"停止DAG运行失败: {terminate_response.status_code} - {terminate_response.text}"
                        )

                return {
                    "status": True,
                    "message": f"已停止 {stopped_count}/{len(dag_runs)} 个运行中的任务实例",
                    "dag_id": dag_id,
                    "stopped_count": stopped_count,
                    "total_count": len(dag_runs),
                }

        except Exception as e:
            logger.error(f"停止数据同步任务失败: {str(e)}")
            return {"status": False, "message": f"停止失败: {str(e)}", "dag_id": dag_id}
