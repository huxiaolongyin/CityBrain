import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from tortoise import fields, models


class BaseModel(models.Model):
    async def to_dict(
        self,
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        m2m: bool = False,
    ) -> Dict[str, Any]:
        """
        将模型对象转换为字典，属性名转换为小驼峰命名法

        Args:
            include_fields: 需要包含的字段列表，为None时包含所有字段
            exclude_fields: 需要排除的字段列表，为None时不排除任何字段
            m2m: 是否包含多对多字段

        Returns:
            Dict[str, Any]: 包含模型数据的字典
        """
        # 初始化字段集合
        include_set: Set[str] = set(include_fields or [])
        exclude_set: Set[str] = set(exclude_fields or [])

        # 优化：预先获取字段列表
        db_fields = self._meta.db_fields
        result: Dict[str, Any] = {}

        # 处理普通字段
        for field in db_fields:
            # 如果字段应该包含在结果中
            if (not include_set or field in include_set) and field not in exclude_set:
                value = getattr(self, field)

                # 根据字段类型进行格式化
                if isinstance(value, datetime):
                    value = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, UUID):
                    value = str(value)
                elif isinstance(value, Enum):
                    value = value.value

                # 使用小驼峰命名法
                result[to_lower_camel_case(field)] = value

        # 处理多对多字段
        if m2m:
            await self._process_m2m_fields(result, include_set, exclude_set)

        return result

    async def _process_m2m_fields(
        self, result: Dict[str, Any], include_set: Set[str], exclude_set: Set[str]
    ) -> None:
        """处理多对多字段，供to_dict方法调用"""
        for field in self._meta.m2m_fields:
            if (not include_set or field in include_set) and field not in exclude_set:
                # 获取关联对象
                related_objects = await getattr(self, field).all().values()
                processed_values = []

                # 处理每个关联对象
                for value in related_objects:
                    processed_value = {}
                    for k, v in value.items():
                        # 格式化值
                        if isinstance(v, datetime):
                            v = v.strftime("%Y-%m-%d %H:%M:%S")
                        elif isinstance(v, UUID):
                            v = str(v)
                        elif isinstance(v, Enum):
                            v = v.value

                        # 转换为小驼峰命名
                        processed_value[to_lower_camel_case(k)] = v
                    processed_values.append(processed_value)

                # 添加到结果字典
                result[to_lower_camel_case(field)] = processed_values


def to_lower_camel_case(x):
    """
    转小驼峰法命名, 首单词首字母小写, 其他单词首字母大写, userLoginCount
    :param x:
    :return:
    """
    s = re.sub("_([a-zA-Z])", lambda m: (m.group(1).upper()), x)
    return s[0].lower() + s[1:]


class TimestampMixin:
    """
    时间戳混入类

    为模型添加创建时间和更新时间字段
    """

    create_time = fields.DatetimeField(
        auto_now_add=True, use_tz=True, description="创建时间"
    )
    update_time = fields.DatetimeField(
        auto_now=True, use_tz=True, description="更新时间"
    )
