#!/usr/bin/env python3
"""
每隔一定时间, 生成模拟的设备数据，并将其插入到MongoDB数据库中。
"""
import argparse
import datetime
import random
import time

import pymongo
from faker import Faker

# 初始化Faker，用于生成随机数据
fake = Faker("zh_CN")

# 设备类型及其对应的数据模板
DEVICE_TYPES = {
    "camera": {
        "status": ["online", "offline", "fault", "maintenance"],
        "metrics": ["resolution", "frame_rate", "storage_usage", "uptime"],
        "locations": ["intersection", "highway", "park", "building_entrance"],
    },
    "traffic_light": {
        "status": ["online", "offline", "fault", "maintenance"],
        "metrics": ["cycle_time", "queue_length", "wait_time", "power_consumption"],
        "signal_types": ["red", "yellow", "green"],
    },
    "environmental_sensor": {
        "status": ["online", "offline", "fault", "calibrating"],
        "metrics": ["temperature", "humidity", "pm25", "pm10", "no2", "o3", "co"],
        "installation_types": ["pole", "building", "underground"],
    },
    "smart_streetlight": {
        "status": ["online", "offline", "fault", "dimmed"],
        "metrics": ["brightness", "power_consumption", "motion_detection_count"],
        "control_modes": ["automatic", "manual", "scheduled"],
    },
}

# 区域和位置信息
DISTRICTS = [
    "朝阳区",
    "海淀区",
    "丰台区",
    "东城区",
    "西城区",
    "石景山区",
    "通州区",
    "昌平区",
]
STREETS = [
    "长安街",
    "建国路",
    "学院路",
    "玉泉路",
    "北四环",
    "南三环",
    "东五环",
    "西二环",
]


def generate_device_id(device_type, index):
    """生成设备ID"""
    prefix = device_type[:3].upper()
    return f"{prefix}-{str(index).zfill(6)}"


def generate_ip():
    """生成随机IP地址"""
    return f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"


def generate_location():
    """生成随机位置信息"""
    district = random.choice(DISTRICTS)
    street = random.choice(STREETS)
    return {
        "district": district,
        "street": street,
        "latitude": round(39.9 + random.uniform(-0.1, 0.1), 6),
        "longitude": round(116.3 + random.uniform(-0.1, 0.1), 6),
    }


def generate_device_data(device_type, device_id, timestamp):
    """根据设备类型生成随机数据"""
    device_template = DEVICE_TYPES[device_type]

    # 基础数据
    data = {
        "device_id": device_id,
        "timestamp": timestamp,
        "device_type": device_type,
        "ip_address": generate_ip(),
        "status": random.choice(device_template["status"]),
        "location": generate_location(),
        "install_date": fake.date_between(start_date="-3y", end_date="-1m").strftime(
            "%Y-%m-%d"
        ),
        "last_maintenance": fake.date_between(
            start_date="-6m", end_date="today"
        ).strftime("%Y-%m-%d"),
    }

    # 设备特定指标
    metrics = {}
    for metric in device_template["metrics"]:
        metrics[metric] = round(random.uniform(0, 100), 2)

    data["metrics"] = metrics

    # 额外设备特定属性
    if device_type == "camera":
        data["location_type"] = random.choice(device_template["locations"])
        data["storage_remaining"] = f"{random.randint(10, 90)}%"
        data["streaming_quality"] = random.choice(["高清", "标清", "超清"])

    elif device_type == "traffic_light":
        data["current_signal"] = random.choice(device_template["signal_types"])
        data["cycle_count"] = random.randint(100, 10000)
        data["intersection_id"] = f"INT-{random.randint(1000, 9999)}"

    elif device_type == "environmental_sensor":
        data["installation_type"] = random.choice(device_template["installation_types"])
        data["battery_level"] = f"{random.randint(10, 100)}%"
        data["last_calibration"] = fake.date_between(
            start_date="-1y", end_date="today"
        ).strftime("%Y-%m-%d")

    elif device_type == "smart_streetlight":
        data["control_mode"] = random.choice(device_template["control_modes"])
        data["light_level"] = random.randint(0, 100)
        data["energy_saved"] = round(random.uniform(0, 50), 2)

    # 随机添加一些告警信息
    if random.random() < 0.05:  # 5%的概率产生告警
        data["alerts"] = [
            {
                "alert_id": f"ALT-{random.randint(10000, 99999)}",
                "severity": random.choice(["低", "中", "高", "紧急"]),
                "message": random.choice(
                    [
                        "设备离线",
                        "电池电量低",
                        "存储空间不足",
                        "传感器读数异常",
                        "网络连接不稳定",
                        "固件版本过低",
                        "设备重启",
                        "硬件故障",
                    ]
                ),
                "timestamp": timestamp,
            }
        ]

    return data


def generate_and_insert_data(mongo_client, db_name, collection_name, device_count):
    """生成并插入模拟数据到MongoDB"""
    db = mongo_client[db_name]
    collection = db[collection_name]

    # 如果集合不存在则创建
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)

    # 为每种设备类型创建设备
    devices = []
    for device_type in DEVICE_TYPES:
        for i in range(1, device_count + 1):
            devices.append(
                {"type": device_type, "id": generate_device_id(device_type, i)}
            )

    total_records = 0

    while True:
        batch = []
        for device in devices:
            record_count = random.randint(1, 5)
            timestamp = datetime.datetime.now()
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            for _ in range(record_count):
                data = generate_device_data(device["type"], device["id"], timestamp_str)
                batch.append(data)

        collection.insert_many(batch)
        total_records += len(batch)
        print(f"累计已插入 {total_records} 条记录...")
        time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成智能设备模拟数据并存入MongoDB")
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://root:example@127.0.0.1:27017/?replicaSet=rs0&authSource=admin&directConnection=true",
        help="MongoDB连接URI",
    )
    parser.add_argument("--db-name", default="city_brain", help="数据库名称")
    parser.add_argument("--collection", default="device_data", help="集合名称")
    parser.add_argument(
        "--devices", type=int, default=20, help="每种设备类型的设备数量"
    )

    args = parser.parse_args()

    try:
        # 连接MongoDB
        client = pymongo.MongoClient(args.mongo_uri)
        client.admin.command("ping")  # 检查连接
        print("MongoDB连接成功")

        # 生成并插入数据
        generate_and_insert_data(
            client,
            args.db_name,
            args.collection,
            args.devices,
        )

    except Exception as e:
        print(f"错误: {e}")
    finally:
        if "client" in locals():
            client.close()
