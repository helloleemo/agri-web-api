import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.schema import ApiResponse
from app.modules.orders import service
from app.modules.orders.schema import OrderCreate, OrderResponse, OrderUpdate
from app.modules.common.response import created, deleted, ok

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=ApiResponse[list[OrderResponse]])
def list_orders(
	skip: int = Query(0, ge=0),
	limit: int = Query(10, ge=1),
	db: Session = Depends(get_db),
):
	orders = service.list_orders(db, skip=skip, limit=limit)
	return ok(orders, "orders fetched")


@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
	order = service.get_order_by_id(db, order_id)
	if not order:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

	return ApiResponse[OrderResponse](
		success=True,
		message="order fetched",
		data=order,
	)


@router.post("", response_model=ApiResponse[OrderResponse], status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
	order = service.create_order(db, payload)
	return ApiResponse[OrderResponse](
		success=True,
		message="order created",
		data=order,
	)


@router.patch("/{order_id}", response_model=ApiResponse[OrderResponse])
def update_order(order_id: uuid.UUID, payload: OrderUpdate, db: Session = Depends(get_db)):
	order = service.update_order(db, order_id, payload)
	if not order:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

	return ApiResponse[OrderResponse](
		success=True,
		message="order updated",
		data=order,
	)


@router.delete("/{order_id}", response_model=ApiResponse[dict[str, str]])
def delete_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
	deleted = service.delete_order(db, order_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

	return ApiResponse[dict[str, str]](
		success=True,
		message="order deleted",
		data={"id": str(order_id)},
	)
