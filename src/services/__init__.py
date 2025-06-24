from .collect_service import CollectService
from .database_service import DatabaseService
from .security_audit_service import SecurityAuditsService

# 实例化服务，方便导入使用
database_service = DatabaseService()
collect_service = CollectService()
security_audits_service = SecurityAuditsService()

# 导出所有服务类
__all__ = [
    "DatabaseService",
    "CollectService",
    "SecurityAuditsService",
    "database_service",
    "collect_service",
    "security_audits_service",
]
