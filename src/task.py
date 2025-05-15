# import json
# import os
# from datetime import datetime
# from typing import Optional

# from apscheduler.schedulers.background import BackgroundScheduler
# from pyspark.sql.functions import col

# from config import Config
# from api.v1.database import MetricDatabase
# from kafka_handler import KafkaHandler
# from logger import get_logger
# from spark_manager import SparkManager

# logger = get_logger(__name__)


# class TaskState:
#     def __init__(self, state_dir: str):
#         self.state_dir = state_dir
#         os.makedirs(state_dir, exist_ok=True)

#     def get_last_id(self, task_name: str, default: int = 0) -> int:
#         state_file = os.path.join(self.state_dir, f"{task_name}.json")
#         if os.path.exists(state_file):
#             with open(state_file, "r") as f:
#                 state = json.load(f)
#                 return state.get("last_id", default)
#         return default

#     def update_last_id(self, task_name: str, last_id: int):
#         state_file = os.path.join(self.state_dir, f"{task_name}.json")
#         state = {"last_id": last_id, "updated_at": datetime.now().isoformat()}
#         if os.path.exists(state_file):
#             with open(state_file, "r") as f:
#                 existing_state = json.load(f)
#                 state.update(existing_state)
#                 state["last_id"] = last_id
#                 state["updated_at"] = datetime.now().isoformat()

#         with open(state_file, "w") as f:
#             json.dump(state, f)

#     def is_task_enabled(self, task_name: str) -> bool:
#         state_file = os.path.join(self.state_dir, f"{task_name}.json")
#         if os.path.exists(state_file):
#             with open(state_file, "r") as f:
#                 state = json.load(f)
#                 return state.get("enabled", False)
#         return False

#     def set_task_enabled(self, task_name: str, enabled: bool):
#         state_file = os.path.join(self.state_dir, f"{task_name}.json")
#         state = {"enabled": enabled, "updated_at": datetime.now().isoformat()}
#         if os.path.exists(state_file):
#             with open(state_file, "r") as f:
#                 existing_state = json.load(f)
#                 state.update(existing_state)
#                 state["enabled"] = enabled
#                 state["updated_at"] = datetime.now().isoformat()

#         with open(state_file, "w") as f:
#             json.dump(state, f)


# class SyncTaskProcessor:
#     def __init__(
#         self,
#         config: Config,
#         spark_manager: SparkManager,
#         task_state: TaskState,
#         kafka_handler: KafkaHandler,
#     ):
#         self.config = config
#         self.spark = spark_manager.spark
#         self.task_state = task_state
#         self.kafka_handler = kafka_handler
#         self.db_config = config.database_config

#     def process_task(self, task_config):
#         task_name = task_config["name"]
#         logger.info(f"Processing sync task: {task_name}")

#         # Get last processed ID
#         last_id = self.task_state.get_last_id(task_name)

#         # Prepare SQL query with last ID
#         query = task_config["query"]["sql"].format(last_id=last_id)

#         # Read from Dameng database
#         df = (
#             self.spark.read.format("jdbc")
#             .option("url", self.db_config["url"])
#             .option("user", self.db_config["user"])
#             .option("password", self.db_config["password"])
#             .option("driver", self.db_config["driver"])
#             .option("query", query)
#             .load()
#         )

#         if df.isEmpty():
#             logger.info(f"No new data for task: {task_name}")
#             return

#         # Extract columns and prepare data for Kafka
#         value_columns = task_config["value_columns"]
#         key_column = task_config["key_column"]
#         id_column = task_config["id_column"]

#         # Process each row
#         rows = df.select(value_columns).collect()
#         max_id = df.agg({id_column: "max"}).collect()[0][0]

#         # Send data to Kafka
#         for row in rows:
#             row_dict = row.asDict()
#             key = row_dict[key_column]
#             self.kafka_handler.send_message(task_config["topic"], key, row_dict)

#         # Update last processed ID
#         self.task_state.update_last_id(task_name, max_id)
#         logger.info(
#             f"Processed {len(rows)} records for task: {task_name}, updated last_id to {max_id}"
#         )


# class MetricTaskProcessor:
#     def __init__(
#         self,
#         config: Config,
#         spark_manager: SparkManager,
#         task_state: TaskState,
#         metric_db: MetricDatabase,
#     ):
#         self.config = config
#         self.spark = spark_manager.spark
#         self.task_state = task_state
#         self.metric_db = metric_db
#         self.db_config = config.database_config

#     def process_task(self, task_config):
#         task_name = task_config["table"]
#         logger.info(f"Processing metric task: {task_name}")

#         # Get last processed ID
#         last_id = self.task_state.get_last_id(task_name)

#         # Prepare SQL query with last ID
#         query = task_config["query"]["sql"].format(last_id=last_id)

#         # Read from Dameng database
#         df = (
#             self.spark.read.format("jdbc")
#             .option("url", self.db_config["url"])
#             .option("user", self.db_config["user"])
#             .option("password", self.db_config["password"])
#             .option("driver", self.db_config["driver"])
#             .option("query", query)
#             .load()
#         )

#         if df.isEmpty():
#             logger.info(f"No new data for metric task: {task_name}")
#             return

#         # Apply transformers if defined
#         if "transformers" in task_config:
#             for transformer in task_config["transformers"]:
#                 if transformer["type"] == "datetime":
#                     for column in transformer["columns"]:
#                         # Convert datetime strings to standard format
#                         df = df.withColumn(column, col(column).cast("string"))

#         # Process metrics
#         rows = df.collect()
#         metrics = [row.asDict() for row in rows]

#         # Store metrics in SQLite database
#         try:
#             self.metric_db.store_metrics(task_name, metrics)

#             # Update last processed ID
#             max_id = df.agg({task_config["id_column"]: "max"}).collect()[0][0]
#             self.task_state.update_last_id(task_name, max_id)

#         except Exception as e:
#             logger.error(f"Error storing metrics: {e}")

#         logger.info(
#             f"Processed {len(metrics)} metrics for task: {task_name}, updated last_id to {max_id}"
#         )


# class TaskManager:
#     def __init__(self, config_path: str = "config.yml"):
#         self.config = Config(config_path)
#         self.task_state = TaskState(self.config.state_dir)
#         self.metric_db = MetricDatabase(self.config.metric_database, self.config)
#         self.kafka_handler = KafkaHandler(self.config.kafka_config["bootstrap_servers"])
#         self.spark_manager = SparkManager(self.config)
#         self.spark_manager.set_log_level(self.config.spark_config["log_level"])

#         self.sync_processor = SyncTaskProcessor(
#             self.config, self.spark_manager, self.task_state, self.kafka_handler
#         )

#         self.metric_processor = MetricTaskProcessor(
#             self.config, self.spark_manager, self.task_state, self.metric_db
#         )

#         self.scheduler = BackgroundScheduler()
#         self.job_ids = {}  # 存储任务ID映射
#         self._schedule_tasks()

#         self.running = False

#     def _schedule_tasks(self):
#         # 调度同步任务（但默认不执行）
#         for task in self.config.sync_tasks:
#             task_name = task["name"]
#             interval = task["schedule"]["interval_seconds"]
#             job_id = f"sync_{task_name}"

#             # 创建任务但设置为暂停状态
#             self.scheduler.add_job(
#                 self.sync_processor.process_task,
#                 "interval",
#                 seconds=interval,
#                 args=[task],
#                 id=job_id,
#                 next_run_time=None,  # 设置为None表示不自动运行
#             )
#             self.job_ids[task_name] = job_id

#         # 调度指标任务（但默认不执行）
#         for task in self.config.metric_tasks:
#             task_name = task["name"]
#             interval = task["schedule"]["interval_seconds"]
#             job_id = f"metric_{task_name}"

#             # 创建任务但设置为暂停状态
#             self.scheduler.add_job(
#                 self.metric_processor.process_task,
#                 "interval",
#                 seconds=interval,
#                 args=[task],
#                 id=job_id,
#                 next_run_time=None,  # 设置为None表示不自动运行
#             )
#             self.job_ids[task_name] = job_id

#     def start(self):
#         if not self.running:
#             self.scheduler.start()
#             self.running = True

#             # 恢复之前启用的任务
#             for task_name, job_id in self.job_ids.items():
#                 if self.task_state.is_task_enabled(task_name):
#                     job = self.scheduler.get_job(job_id)
#                     if job and job.next_run_time is None:
#                         self.scheduler.resume_job(job_id)

#             logger.info("Task manager started")

#     def stop(self):
#         if self.running:
#             self.scheduler.shutdown()
#             self.kafka_handler.close()
#             self.spark_manager.close()
#             self.running = False
#             logger.info("Task manager stopped")

#     def start_task(self, task_name: str):
#         """启动任务的自动执行"""
#         if task_name in self.job_ids:
#             job_id = self.job_ids[task_name]
#             job = self.scheduler.get_job(job_id)

#             if job and job.next_run_time is None:
#                 self.scheduler.resume_job(job_id)
#                 self.task_state.set_task_enabled(task_name, True)
#                 logger.info(f"Task {task_name} has been started")
#                 return True
#         return False

#     def stop_task(self, task_name: str):
#         """停止任务的自动执行"""
#         if task_name in self.job_ids:
#             job_id = self.job_ids[task_name]
#             job = self.scheduler.get_job(job_id)

#             if job and job.next_run_time is not None:
#                 self.scheduler.pause_job(job_id)
#                 self.task_state.set_task_enabled(task_name, False)
#                 logger.info(f"Task {task_name} has been stopped")
#                 return True
#         return False

#     def run_sync_task(self, task_name: str):
#         for task in self.config.sync_tasks:
#             if task["name"] == task_name:
#                 self.sync_processor.process_task(task)
#                 return True
#         return False

#     def run_metric_task(self, task_name: str):
#         for task in self.config.metric_tasks:
#             if task["name"] == task_name:
#                 self.metric_processor.process_task(task)
#                 return True
#         return False

#     def get_metrics(
#         self,
#         start_date: str,
#         end_date: str,
#         device_code: Optional[str] = None,
#         task_type: Optional[str] = None,
#     ):
#         return self.metric_db.query_robot_task_metrics(
#             start_date, end_date, device_code, task_type
#         )
