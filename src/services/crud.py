from typing import Generic, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel
from pydantic.main import IncEx
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

# 创建一个泛型类型变量
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用CRUD操作工厂类
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD工厂

        Args:
            model: Tortoise模型类
        """
        self.model = model

    async def get(self, id: int) -> Optional[ModelType]:
        """
        通过ID获取记录

        Args:
            id: 记录ID

        Returns:
            记录字典

        Raises:
            ValueError: 记录不存在
        """
        obj = await self.model.get_or_none(id=id)
        if not obj:
            raise ValueError("记录不存在")

        return obj

    async def get_list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: Optional[List[str]] = None,
        prefetch: Optional[List[str]] = None,
        exclude: list = None,
    ) -> Tuple[int, List[dict]]:
        """
        获取多条记录

        Args:
            skip: 跳过记录数
            limit: 返回记录数限制
            filters: 过滤条件

        Returns:
            记录列表
        """
        # 过滤
        query = self.model.filter(search)

        # 查询总数
        total = await query.count()

        if total == 0:
            return total, []

        # 分页查询
        query = query.limit(page_size).offset((page - 1) * page_size)

        # 关联预加载
        if prefetch:
            query = query.prefetch_related(*prefetch)

        # 排序
        order = order or []
        if order:
            query = query.order_by(*order)

        objs = await query.all()
        result = []
        for obj in objs:
            records = await obj.to_dict(exclude_fields=exclude)
            result.append(records)

        return total, result

    def get_all(self) -> QuerySet[ModelType]:
        """
        获取查询集

        Returns:
            查询集对象
        """
        return self.model.all()

    async def create(
        self,
        obj_in: CreateSchemaType,
        exclude: IncEx = None,
        unique_field: str = None,
        unique_field_error_message: str = None,
    ) -> ModelType:
        """
        创建新记录
        Args:
            obj_in: 包含创建数据的字典
            exclude: 排除的字段
            unique_field: 需要检查唯一性的字段名
            unique_field_error_message: 唯一性检查失败时的错误消息
        Returns:
            创建的模型实例
        """
        # 转换输入数据为字典
        if isinstance(obj_in, dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(
                exclude_unset=True, exclude_none=True, exclude=exclude
            )

        # 唯一性检查
        if unique_field and unique_field in obj_dict:
            filter_kwargs = {unique_field: obj_dict[unique_field]}
            if await self.model.filter(**filter_kwargs).first():
                error_msg = unique_field_error_message or f"{unique_field}已存在"
                raise ValueError(error_msg)

        # 创建并保存对象
        obj: ModelType = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        exclude: IncEx = None,
    ) -> Optional[ModelType]:
        """
        更新记录

        Args:
            id: 记录ID
            obj_in: 包含更新数据的字典

        Returns:
            更新后的模型实例，如果不存在则返回None
        """

        if isinstance(obj_in, dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(
                exclude_unset=True, exclude_none=True, exclude=exclude
            )

        obj = await self.get(id)

        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def delete(self, id: int) -> bool:
        """
        删除记录

        Args:
            id: 记录ID

        Returns:
            删除是否成功
        """
        obj = await self.get(id)
        await obj.delete()
