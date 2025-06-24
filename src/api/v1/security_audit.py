from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from tortoise.expressions import Q

from models.security_audit import SecurityAudit
from schemas.common import Error, Success
from schemas.security_audit import SecurityAuditCreate
from services import SecurityAuditsService, security_audits_service

router = APIRouter()


def get_security_audits_service() -> SecurityAuditsService:
    return security_audits_service


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


@router.post("/security-audits", summary="创建安全审计申请")
async def create_security_audit(request: Request, audit_request: SecurityAuditCreate):
    """
    创建安全审计申请
    用户申请访问特定数据时需要填写此表单
    """
    try:
        # 获取请求信息
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # 创建审计记录
        audit_data = {
            **audit_request.model_dump(),
            "ip_address": client_ip,
            "user_agent": user_agent,
            "request_method": request.method,
            "request_url": str(request.url),
        }

        audit_record = await SecurityAudit.create(**audit_data)

        return Success(data={"auditId": audit_record.id}, msg="创建审计申请成功")

    except Exception as e:
        return Error(message=f"创建审计申请失败: {str(e)}")


@router.get("/security-audits", summary="查询安全审计记录")
async def get_security_audits(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量", alias="pageSize"),
    query_user: Optional[str] = Query(None, description="查询人", alias="queryUser"),
    query_indicator: Optional[str] = Query(
        None, description="查询指标", alias="queryIndicator"
    ),
    start_date: Optional[str] = Query(
        None, description="记录创建开始日期, 格式: YYYY-MM-DD", alias="startDate"
    ),
    end_date: Optional[str] = Query(
        None, description="记录创建结束日期, 格式: YYYY-MM-DD", alias="endDate"
    ),
    ip_address: Optional[str] = Query(None, description="IP地址", alias="ipAddress"),
    security_audits_service: SecurityAuditsService = Depends(
        get_security_audits_service
    ),
):
    """
    查询安全审计记录
    支持按查询人、审核状态、查询指标等条件筛选
    """
    try:
        # 构建查询条件
        q = Q()

        if query_user:
            q &= Q(query_user__icontains=query_user)
        if query_indicator:
            q &= Q(query_indicator__icontains=query_indicator)
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            q &= Q(create_time__gte=start_date)
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            q &= Q(create_time__lte=end_date)
        if ip_address:
            q &= Q(ip_address=ip_address)

        # 查询总数
        total, security_audits_list = await security_audits_service.get_list(
            page, page_size, q
        )

        # 查询今日审计访问记录和异常访问记录
        today_q = Q(create_time__gte=datetime.today().date())
        today_access_total, _ = await security_audits_service.get_list(1, 9999, today_q)
        abnormal_access_total, _ = await security_audits_service.get_list(
            1, 9999, Q(ip_address__isnull=True)
        )
        today_abnormal_access_total, _ = await security_audits_service.get_list(
            1, 9999, today_q & Q(ip_address__isnull=True)
        )

        return Success(
            msg="获取安全审计记录成功",
            data={
                "records": security_audits_list,
                "total": total,
                "page": page,
                "pageSize": page_size,
                "todayAccessTotal": today_access_total,
                "todayAbnormalAccessTotal": today_abnormal_access_total,
                "accessTotal": total,
                "abnormalAccessTotal": abnormal_access_total,
            },
        )

    except Exception as e:
        return Error(message=f"查询审计记录失败: {str(e)}")
