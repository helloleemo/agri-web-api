import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import AuthUser, get_auth_context, require_roles
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error, raise_not_found_order
from app.modules.common.messages import OrderMessages
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.orders import service
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate
from app.modules.roles.constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_STAFF

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=ApiResponse[list[OrderResponse]], response_model_exclude_none=True)
def list_orders(
	skip: int = Query(0, ge=0),
	limit: int = Query(10, ge=1),
	auth: AuthUser = Depends(require_roles([ROLE_ADMIN, ROLE_STAFF])),
	db: Session = Depends(get_db),
):
	orders = service.list_orders(db, skip=skip, limit=limit)
	return ok(orders, OrderMessages.LIST)


@router.get("/{order_id}", response_model=ApiResponse[OrderResponse], response_model_exclude_none=True)
def get_order(
	order_id: uuid.UUID,
	auth: AuthUser = Depends(require_roles([ROLE_ADMIN, ROLE_STAFF])),
	db: Session = Depends(get_db),
):
	order = service.get_order_by_id(db, order_id)
	if not order:
		raise_not_found_order(str(order_id))

	return ok(order, OrderMessages.GET)


@router.post("", response_model=ApiResponse[OrderResponse], status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_order(
	payload: OrderCreate,
	auth: AuthUser = Depends(get_auth_context),
	db: Session = Depends(get_db),
):
	if auth.role_code == ROLE_CUSTOMER and payload.user_id != auth.id:
		raise_error(ErrorCode.FORBIDDEN, detail="Customers can only create their own orders")

	order = service.create_order(db, payload)
	return created(order, OrderMessages.CREATE)


@router.patch("/{order_id}", response_model=ApiResponse[OrderResponse], response_model_exclude_none=True)
def update_order(
	order_id: uuid.UUID,
	payload: OrderUpdate,
	auth: AuthUser = Depends(require_roles([ROLE_ADMIN, ROLE_STAFF])),
	db: Session = Depends(get_db),
):
	order = service.update_order(db, order_id, payload)
	if not order:
		raise_not_found_order(str(order_id))

	return ok(order, OrderMessages.UPDATE)


@router.delete("/{order_id}", response_model=ApiResponse[dict[str, str]], response_model_exclude_none=True)
def delete_order(
	order_id: uuid.UUID,
	auth: AuthUser = Depends(require_roles([ROLE_ADMIN, ROLE_STAFF])),
	db: Session = Depends(get_db),
):
	is_deleted = service.delete_order(db, order_id)
	if not is_deleted:
		raise_not_found_order(str(order_id))

	return deleted(str(order_id), OrderMessages.DELETE)
