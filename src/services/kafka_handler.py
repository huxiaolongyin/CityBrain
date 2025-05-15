import json
from datetime import datetime

from kafka import KafkaConsumer, KafkaProducer, TopicPartition

from logger import get_logger

logger = get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class KafkaHandler:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda x: json.dumps(x, cls=DateTimeEncoder).encode(
                    "utf-8"
                ),
                key_serializer=lambda x: str(x).encode("utf-8"),
            )
            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset="earliest",
                consumer_timeout_ms=10000,
                # 其他必要的配置
            )
        except Exception as e:
            logger.error(f"初始化 KafkaProducer 和 KafkaConsumer 时出错: {e}")

    def send_message(self, topic: str, key, value):
        logger.debug(f"开始发送消息: topic={topic}, key={key}, value={value}")
        try:
            self.producer.send(topic, key=key, value=value)
            logger.debug(f"消息发送完成: topic={topic}, key={key}, value={value}")
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")

    def close(self):
        self.producer.close()

    def consume_messages(self, topic, max_messages=1000, start_offset=None):
        logger.debug(
            f"开始消费消息: topic={topic}, max_messages={max_messages}, start_offset={start_offset}"
        )
        try:
            # 为主题分区分配消费者
            partition = TopicPartition(topic, 0)  # 假设只有一个分区
            self.consumer.assign([partition])

            # 如果提供了起始偏移量，设置消费者位置
            if start_offset is not None:
                self.consumer.seek(
                    partition, start_offset + 1
                )  # 从上次处理的下一条开始

            messages = []
            for i, message in enumerate(self.consumer):
                if i >= max_messages:
                    break
                messages.append(message)

            self.consumer.close()
            return messages

        except Exception as e:
            logger.error(f"消费消息时出错: {e}")
            return []
