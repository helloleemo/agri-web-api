from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import AuthUser, get_auth_context
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.common.messages import CommonMessages
from app.modules.common.response import ok
from app.modules.common.schema import ApiResponse
from app.modules.order_statuses import service
from app.modules.order_statuses.schema import OrderStatusEmailTemplateUpdate, OrderStatusResponse
from app.modules.roles.constants import RoleCode


router = APIRouter(prefix="/order-statuses", tags=["Order Statuses"])


@router.get("", response_model=ApiResponse[list[OrderStatusResponse]], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def list_order_statuses(
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    _ = auth
    statuses = service.list_order_statuses(db)
    return ok(statuses, CommonMessages.OK)


@router.patch(
    "/{code}/email-template",
    response_model=ApiResponse[OrderStatusResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def update_order_status_email_template(
    code: int,
    payload: OrderStatusEmailTemplateUpdate,
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    if auth.role_code not in {RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value}:
        raise_error(ErrorCode.FORBIDDEN, detail="Only admin/staff can update order email templates")

    updated = service.update_order_status_email_templates(db, code=code, payload=payload)
    if not updated:
        raise_error(ErrorCode.NOT_FOUND, detail=f"Order status code {code} not found")
    return ok(updated, CommonMessages.OK)
