from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.messages import CommonMessages
from app.modules.common.response import ok
from app.modules.common.schema import ApiResponse
from app.modules.order_statuses import service
from app.modules.order_statuses.schema import OrderStatusResponse


router = APIRouter(prefix="/order-statuses", tags=["Order Statuses"])


@router.get("", response_model=ApiResponse[list[OrderStatusResponse]], response_model_exclude_none=True, status_code=status.HTTP_200_OK)
def list_order_statuses(db: Session = Depends(get_db)):
    statuses = service.list_order_statuses(db)
    return ok(statuses, CommonMessages.OK)
