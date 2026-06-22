from typing import Any, NoReturn

from app.modules.common.error_code import ErrorCode
from app.modules.common.error_catalog import get_error_spec


class AppError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        *,
        detail: str | None = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ):
        spec = get_error_spec(code)
        self.status_code = spec.http_status
        self.code = spec.code.value
        self.message = message or spec.message
        self.detail = detail or spec.detail
        self.meta = meta or {}
        super().__init__(self.detail)


def raise_error(code: ErrorCode, *, detail: str | None = None, message: str | None = None, meta: dict | None = None) -> NoReturn:
    raise AppError(code=code, detail=detail, message=message, meta=meta)


def raise_not_found_user(user_id: str | None = None) -> NoReturn:
    detail = f"User not found: {user_id}" if user_id else None
    raise_error(ErrorCode.USER_NOT_FOUND, detail=detail)


def raise_not_found_product(product_id: str | None = None) -> NoReturn:
    detail = f"Product not found: {product_id}" if product_id else None
    raise_error(ErrorCode.PRODUCT_NOT_FOUND, detail=detail)


def raise_not_found_order(order_id: str | None = None) -> NoReturn:
    detail = f"Order not found: {order_id}" if order_id else None
    raise_error(ErrorCode.ORDER_NOT_FOUND, detail=detail)

def raise_not_found_category(category_id: str | None = None) -> NoReturn:
    detail = f"Category not found: {category_id}" if category_id else None
    raise_error(ErrorCode.CATEGORY_NOT_FOUND, detail=detail)

def raise_not_found_unit(unit_id: str | None = None) -> NoReturn:
    detail = f"Unit not found: {unit_id}" if unit_id else None
    raise_error(ErrorCode.UNIT_NOT_FOUND, detail=detail)

def raise_not_found_image(image_id: str | None = None) -> NoReturn:
    detail = f"Image not found: {image_id}" if image_id else None
    raise_error(ErrorCode.IMAGE_NOT_FOUND, detail=detail)