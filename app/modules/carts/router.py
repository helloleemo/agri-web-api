from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import AuthUser, get_auth_context
from app.modules.carts import crud
from app.modules.carts.schema import CartResponse, CartSyncPayload
from app.modules.common.messages import CartMessages
from app.modules.common.response import ok
from app.modules.common.schema import ApiResponse

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=ApiResponse[CartResponse], response_model_exclude_none=True)
def get_cart(
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    cart = crud.get_cart(db, auth.id)
    db.commit()
    return ok(cart, CartMessages.GET)


@router.put("", response_model=ApiResponse[CartResponse], response_model_exclude_none=True)
def sync_cart(
    payload: CartSyncPayload,
    auth: AuthUser = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    cart = crud.sync_cart(db, auth.id, payload.items)
    db.commit()
    return ok(cart, CartMessages.SYNC)
