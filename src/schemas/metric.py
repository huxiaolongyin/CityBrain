from typing import Optional

from pydantic import BaseModel, Field

from api.v1.enums import IndicatorType
from utils.enums import ExportFormat


# 请求和响应模型
class MetricExport(BaseModel):
    start_date: str = Field(
        ...,
        description="开始日期 (YYYY-MM-DD)",
        alias="startDate",
    )

    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)", alias="endDate")
    vin: Optional[str] = Field(None, description="车辆VIN码", alias="vin")
    indicator_type: IndicatorType = Field(
        ..., description="指标类型", alias="indicatorType"
    )

    export_format: ExportFormat = Field(
        ExportFormat.CSV,
        description="导出格式 (csv 或 excel)",
        alias="exportFormat",
    )

    limit: int = Field(10000, description="导出数据条数，默认10000")
