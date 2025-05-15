from .collect_service import CollectService
from .database_service import DatabaseService

# 实例化服务，方便导入使用
database_service = DatabaseService()
collect_service = CollectService()

# 导出所有服务类
__all__ = ["DatabaseService", "CollectService", "database_service", "collect_service"]
