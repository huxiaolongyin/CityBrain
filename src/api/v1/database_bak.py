import decimal
import sqlite3
from datetime import datetime
from typing import Any, Dict, List

from config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


class MetricDatabase:
    def __init__(self, db_path: str, config: Config):
        self.db_path = db_path
        self.config = config
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Dynamically create tables for each metric task
        for metric_task in self.config.metric_tasks:
            task_name = metric_task["table"]
            columns = metric_task["value_columns"]
            key_columns = metric_task.get("key_columns", [])

            # Build the CREATE TABLE SQL statement
            column_defs = []
            for col_name in columns:
                col_type = "TEXT"
                if col_name.endswith("_COUNT") or col_name.endswith("_ID"):
                    col_type = "INTEGER"
                elif col_name.endswith("_DURATION") or col_name.startswith("AVG_"):
                    col_type = "REAL"
                column_defs.append(f"{col_name.lower()} {col_type}")

            # Add created_at column
            column_defs.append("created_at TEXT")

            # Build primary key clause if key columns are specified
            primary_key = ""
            if key_columns:
                primary_key = (
                    f", PRIMARY KEY ({', '.join([k.lower() for k in key_columns])})"
                )

            # Create the table
            table_sql = f"""
            CREATE TABLE IF NOT EXISTS {task_name} (
                {', '.join(column_defs)}{primary_key}
            )
            """

            logger.info(f"Creating table for metric task: {task_name}")
            logger.debug(f"SQL: {table_sql}")
            cursor.execute(table_sql)

        conn.commit()
        conn.close()

    def store_metrics(self, task_name: str, metrics: List[Dict[str, Any]]):
        if not metrics:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get column names from the first metric
            columns = list(metrics[0].keys())
            columns_lower = [col.lower() for col in columns]

            # Add created_at
            columns_lower.append("created_at")
            placeholders = ", ".join(["?"] * (len(columns) + 1))

            # Build the INSERT statement
            insert_sql = f"""
            INSERT OR REPLACE INTO {task_name} 
            ({', '.join(columns_lower)})
            VALUES ({placeholders})
            """

            # Insert each metric
            for metric in metrics:
                # 转换Decimal类型为float
                values = []
                for col in columns:
                    val = metric[col]
                    # 检查是否为Decimal类型并转换
                    if isinstance(val, decimal.Decimal):
                        val = float(val)
                    values.append(val)

                values.append(datetime.now().isoformat())  # Add created_at
                cursor.execute(insert_sql, values)

            conn.commit()
            logger.info(f"Stored {len(metrics)} metrics for task: {task_name}")
        except Exception as e:
            logger.error(f"Error storing metric: {e}")
            logger.error(f"Metric data: {metrics[:1]}")
            conn.rollback()
        finally:
            conn.close()

    def query_metrics(
        self,
        task_name: str,
        start_date: str,
        end_date: str,
        filters: List[Dict[str, Any]] = None,
        timestamp_column: str = None,
        selected_fields: List[str] = None,  # 新增参数，用于指定要选择的字段
    ):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 找到指标任务配置
        timestamp_col = None
        for task in self.config.metric_tasks:
            if task["table"] == task_name:
                # 从配置中获取timestamp_column，现在它是一个字典
                timestamp_col_dict = task.get("timestamp_column")
                timestamp_col = list(timestamp_col_dict.keys())[0].lower()
                break

        # 如果提供了指定的timestamp_column，则使用它
        if timestamp_column:
            timestamp_col = timestamp_column.lower()

        if not timestamp_col:
            raise ValueError(f"无法找到任务的时间戳列: {task_name}")

        # 构建查询 - 如果有指定字段则选择特定字段，否则选择所有字段
        if selected_fields and len(selected_fields) > 0:
            fields_str = ", ".join(selected_fields)
            query = f"""
            SELECT {fields_str}
            FROM {task_name}
            WHERE {timestamp_col} >= ? AND {timestamp_col} <= ?
            """
        else:
            query = f"""
            SELECT *
            FROM {task_name}
            WHERE {timestamp_col} >= ? AND {timestamp_col} <= ?
            """

        params = [start_date, end_date]

        # 添加其他过滤条件
        if filters:
            for filter in filters:
                for key, value in filter.items():
                    if value is not None:
                        query += f" AND {key} = ?"
                        params.append(value)
        logger.debug(f"查询: {query}, 参数: {params}")
        try:
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"查询指标时出错: {e}")
            logger.error(f"查询: {query}, 参数: {params}")
            return []
        finally:
            conn.close()
