from typing import Any, Dict, List, Optional, Union

from tortoise.expressions import Q

from models.collect import Collect
from models.database import Database
from schemas.collect import CollectCreate, CollectUpdate
from utils.enums import Status

from .crud import CRUD


class CollectService(CRUD[Collect, CollectCreate, CollectUpdate]):
    """
    数据同步服务类，提供数据同步任务管理的业务逻辑
    """

    def __init__(self):
        """初始化数据同步服务，使用Collect模型"""
        super().__init__(Collect)

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
        # obj_in.source_id = source_db
        # obj_in.target_id = target_db

        # 创建同步任务
        return await super().create(
            obj_in,
            exclude=[
                "source_name",
                "source_type",
                "target_name",
                "target_type",
            ],
        )

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
        # 检查同步任务是否存在
        await super().get(id=id)

        # 将obj_in转换为字典
        update_data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        # 如果更新了源数据库ID，验证它是否存在
        if "sourceId" in update_data and update_data["sourceId"] is not None:
            source_db = await Database.get_or_none(id=update_data["sourceId"])
            if not source_db:
                raise ValueError(f"数据源ID {update_data['sourceId']} 不存在")

        # 如果更新了目标数据库ID，验证它是否存在
        if "targetId" in update_data and update_data["targetId"] is not None:
            target_db = await Database.get_or_none(id=update_data["targetId"])
            if not target_db:
                raise ValueError(f"目标数据库ID {update_data['targetId']} 不存在")

        # 更新同步任务
        return await super().update(id, obj_in, exclude)

    async def get_by_status(
        self, status: Status, skip: int = 0, limit: int = 100
    ) -> List[Collect]:
        """
        获取指定状态的数据同步任务

        Args:
            status: 状态枚举值
            skip: 跳过记录数
            limit: 返回记录数限制

        Returns:
            满足条件的Collect列表
        """
        return await self.get_multi(skip=skip, limit=limit, status=status)

    async def get_by_database(
        self, database_id: int, skip: int = 0, limit: int = 100
    ) -> List[Collect]:
        """
        获取与指定数据库相关的所有同步任务（作为源或目标）

        Args:
            database_id: 数据库ID
            skip: 跳过记录数
            limit: 返回记录数限制

        Returns:
            与该数据库相关的Collect列表
        """
        queryset = Collect.filter(sourceId=database_id) | Collect.filter(
            targetId=database_id
        )
        return await queryset.offset(skip).limit(limit).all()

    async def start_collect_job(self, id: int) -> Dict[str, Any]:
        """
        启动数据同步任务

        Args:
            id: 同步任务ID

        Returns:
            包含状态和消息的字典
        """
        collect = await self.get(id)
        if not collect:
            return {"status": False, "message": "数据同步任务不存在"}

        if collect.status != Status.ENABLED:
            return {"status": False, "message": "数据同步任务未启用，无法执行"}

        # 这里实现实际启动同步任务的逻辑
        # 例如：提交到任务队列，启动定时任务等
        try:
            # 模拟任务启动逻辑
            return {"status": True, "message": "数据同步任务已提交执行"}
        except Exception as e:
            return {"status": False, "message": f"启动失败: {str(e)}"}
