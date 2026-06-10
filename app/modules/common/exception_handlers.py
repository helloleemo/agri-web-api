from typing import Any, cast
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.modules.common.error_code import ErrorCode
from app.modules.common.error_catalog import get_error_spec
from app.modules.common.errors import AppError
from app.modules.common.schema import ApiResponse

logger = logging.getLogger(__name__)


def _map_integrity_error(exc: IntegrityError) -> tuple[ErrorCode, str]:
    raw = str(getattr(exc, "orig", exc)).lower()

    if "users_email_key" in raw or "key (email)=" in raw:
        return ErrorCode.USER_EMAIL_ALREADY_EXISTS, "Email already exists"
    if "categories_name_key" in raw:
        return ErrorCode.CATEGORY_NAME_ALREADY_EXISTS, "Category name already exists"
    if "orders_order_no_key" in raw:
        return ErrorCode.CONFLICT, "Order number already exists"
    if "duplicate key value violates unique constraint" in raw:
        return ErrorCode.CONFLICT, "Resource already exists"

    return ErrorCode.BAD_REQUEST, "Data integrity constraint violated"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        body = ApiResponse[None](
            success=False,
            message=exc.message,
            data=None,
            code=exc.code,
            detail=exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(exclude_none=True))

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        detail_payload = exc.detail if isinstance(exc.detail, dict) else None

        if detail_payload and "code" in detail_payload and "detail" in detail_payload:
            detail_dict = cast(dict[str, Any], detail_payload)
            code = str(detail_dict["code"])
            detail = str(detail_dict["detail"])
        else:
            code = f"HTTP_{exc.status_code}"
            detail = str(exc.detail)
        body = ApiResponse[None](success=False, message="request failed", data=None, code=code, detail=detail)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump(exclude_none=True))

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, exc: IntegrityError):
        code, detail = _map_integrity_error(exc)
        spec = get_error_spec(code)
        body = ApiResponse[None](
            success=False,
            message=spec.message,
            data=None,
            code=spec.code.value,
            detail=detail,
        )
        return JSONResponse(status_code=spec.http_status, content=body.model_dump(exclude_none=True))

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {exc}", exc_info=True)
        body = ApiResponse[None](
            success=False,
            message="request failed",
            data=None,
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
        return JSONResponse(status_code=500, content=body.model_dump(exclude_none=True))