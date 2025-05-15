import random

from fastapi import APIRouter

router = APIRouter()


# ============= 大数据状态接口 =============
@router.get("/cluster/status", summary="获取大数据集群状态")
async def get_cluster_status():
    """
    获取大数据集群状态，包括设备数、核心数、内存、存储等信息
    """
    # 模拟集群状态数据
    status = [
        {"key": "totalDevices", "name": "总设备数", "value": random.randint(5, 20)},
        {"key": "activeCores", "name": "活跃核心数", "value": random.randint(40, 150)},
        {"key": "totalCores", "name": "总核心数", "value": random.randint(160, 200)},
        {
            "key": "totalMemory",
            "name": "总内存",
            "value": f"{random.randint(500, 1000)}GB",
        },
        {
            "key": "availableMemory",
            "name": "可用内存",
            "value": f"{random.randint(100, 400)}GB",
        },
        {
            "key": "totalStorage",
            "name": "总存储",
            "value": f"{random.randint(50, 200)}TB",
        },
        {
            "key": "usedStorage",
            "name": "已用存储",
            "value": f"{random.randint(10, 100)}TB",
        },
        {
            "key": "usagePercent",
            "name": "使用率",
            "value": f"{random.uniform(30, 90)}%",
        },
    ]
    # "services": [
    #     {
    #         "name": "HDFS",
    #         "status": "健康",
    #         "uptime": "30天12小时45分钟",
    #         "nodes": random.randint(3, 10),
    #     },
    #     {
    #         "name": "YARN",
    #         "status": "健康",
    #         "uptime": "28天9小时30分钟",
    #         "activeApplications": random.randint(1, 20),
    #     },
    #     {
    #         "name": "Spark",
    #         "status": "健康",
    #         "uptime": "25天7小时15分钟",
    #         "activeJobs": random.randint(0, 10),
    #     },
    #     {
    #         "name": "HBase",
    #         "status": "健康",
    #         "uptime": "27天5小时20分钟",
    #         "regions": random.randint(10, 100),
    #     },
    #     {
    #         "name": "Kafka",
    #         "status": random.choice(["健康", "警告"]),
    #         "uptime": "22天18小时50分钟",
    #         "topics": random.randint(5, 50),
    #         "messages": f"{random.randint(1, 999)}K/s",
    #     },

    return {
        "code": 200,
        "success": True,
        "msg": "获取集群状态成功",
        "data": {"records": status},
    }


# @router.get("/cluster/services", summary="获取集群服务状态")
# async def get_cluster_services():
#     """
#     获取大数据集群各服务的详细状态
#     """
#     services = [
#         {
#             "id": 1,
#             "name": "HDFS",
#             "version": "3.3.4",
#             "status": "健康",
#             "startTime": (
#                 datetime.datetime.now()
#                 - datetime.timedelta(days=30, hours=12, minutes=45)
#             ).strftime("%Y-%m-%d %H:%M:%S"),
#             "endpoints": ["http://namenode:9870", "http://datanode1:9864"],
#             "metrics": {
#                 "totalBlocks": random.randint(10000, 1000000),
#                 "corruptBlocks": random.randint(0, 10),
#                 "missingBlocks": random.randint(0, 5),
#                 "underReplicatedBlocks": random.randint(0, 100),
#                 "dfsUsed": f"{random.randint(10, 100)}TB",
#                 "dfsRemaining": f"{random.randint(10, 100)}TB",
#             },
#         },
#         {
#             "id": 2,
#             "name": "YARN",
#             "version": "3.3.4",
#             "status": "健康",
#             "startTime": (
#                 datetime.datetime.now()
#                 - datetime.timedelta(days=28, hours=9, minutes=30)
#             ).strftime("%Y-%m-%d %H:%M:%S"),
#             "endpoints": ["http://resourcemanager:8088"],
#             "metrics": {
#                 "activeNodes": random.randint(3, 10),
#                 "allocatedCores": random.randint(20, 150),
#                 "allocatedMemory": f"{random.randint(100, 800)}GB",
#                 "runningApplications": random.randint(1, 20),
#                 "pendingApplications": random.randint(0, 5),
#             },
#         },
#         {
#             "id": 3,
#             "name": "Spark",
#             "version": "3.3.1",
#             "status": "健康",
#             "startTime": (
#                 datetime.datetime.now()
#                 - datetime.timedelta(days=25, hours=7, minutes=15)
#             ).strftime("%Y-%m-%d %H:%M:%S"),
#             "endpoints": ["http://sparkmaster:8080"],
#             "metrics": {
#                 "activeDrivers": random.randint(0, 5),
#                 "activeExecutors": random.randint(5, 50),
#                 "completedApplications": random.randint(100, 1000),
#                 "runningJobs": random.randint(0, 10),
#             },
#         },
#         {
#             "id": 4,
#             "name": "Kafka",
#             "version": "3.3.1",
#             "status": random.choice(["健康", "警告"]),
#             "startTime": (
#                 datetime.datetime.now()
#                 - datetime.timedelta(days=22, hours=18, minutes=50)
#             ).strftime("%Y-%m-%d %H:%M:%S"),
#             "endpoints": ["kafka1:9092", "kafka2:9092", "kafka3:9092"],
#             "metrics": {
#                 "activeControllers": 1,
#                 "offlinePartitions": random.randint(0, 5),
#                 "underReplicatedPartitions": random.randint(0, 10),
#                 "messageIn": f"{random.randint(1, 999)}K/s",
#                 "bytesIn": f"{random.randint(1, 100)}MB/s",
#                 "bytesOut": f"{random.randint(1, 100)}MB/s",
#             },
#         },
#     ]

#     return {
#         "code": 200,
#         "success": True,
#         "msg": "获取集群服务状态成功",
#         "data": {"records": services},
#     }


# @router.get("/cluster/overview", summary="获取集群资源概览")
# async def get_cluster_overview():
#     """
#     获取集群资源概览，包括CPU、内存、存储、网络等使用情况
#     """
#     # 生成过去24小时的时间序列数据
#     time_series = []
#     start_time = datetime.datetime.now() - datetime.timedelta(hours=24)

#     for hour in range(25):  # 包含当前小时
#         time_point = start_time + datetime.timedelta(hours=hour)
#         time_series.append(
#             {
#                 "timestamp": time_point.strftime("%Y-%m-%d %H:%M:%S"),
#                 "cpuUsage": random.uniform(10, 90),
#                 "memoryUsage": random.uniform(20, 85),
#                 "diskIO": random.uniform(1, 200),
#                 "networkIO": random.uniform(10, 500),
#             }
#         )

#     overview = {
#         "current": {
#             "cpuUsage": random.uniform(30, 80),
#             "memoryUsage": random.uniform(40, 75),
#             "diskUsage": random.uniform(20, 70),
#             "networkTraffic": f"{random.randint(50, 500)}MB/s",
#         },
#         "total": {
#             "nodes": random.randint(5, 20),
#             "cores": random.randint(160, 200),
#             "memory": f"{random.randint(500, 1000)}GB",
#             "storage": f"{random.randint(50, 200)}TB",
#         },
#         "alerts": [
#             {
#                 "level": "警告",
#                 "service": "Kafka",
#                 "message": "Topic 'events' 副本数不足",
#                 "time": (
#                     datetime.datetime.now()
#                     - datetime.timedelta(minutes=random.randint(5, 120))
#                 ).strftime("%Y-%m-%d %H:%M:%S"),
#             },
#             {
#                 "level": "信息",
#                 "service": "HDFS",
#                 "message": "NameNode 已切换为活跃状态",
#                 "time": (
#                     datetime.datetime.now()
#                     - datetime.timedelta(hours=random.randint(1, 12))
#                 ).strftime("%Y-%m-%d %H:%M:%S"),
#             },
#         ],
#         "timeSeries": time_series,
#     }

#     return {
#         "code": 200,
#         "success": True,
#         "msg": "获取集群资源概览成功",
#         "data": {"records": overview},
#     }
