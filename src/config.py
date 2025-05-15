import os

import yaml


class Config:
    def __init__(self, config_path: str = "config.yml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Ensure state directory exists
        os.makedirs(self.config["state_dir"], exist_ok=True)

    @property
    def spark_config(self):
        return self.config["spark"]

    @property
    def database_config(self):
        return self.config["database"]

    @property
    def kafka_config(self):
        return self.config["kafka"]

    @property
    def sync_tasks(self):
        return self.config["sync_tasks"]

    @property
    def metric_tasks(self):
        return self.config["metric_tasks"]

    @property
    def state_dir(self):
        return self.config["state_dir"]

    @property
    def metric_database(self):
        return self.config["metric_database"]
