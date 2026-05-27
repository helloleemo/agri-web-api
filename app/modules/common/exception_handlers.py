from typing import Any, cast
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import AppError
from app.modules.common.schema import ApiResponse

logger = logging.getLogger(__name__)


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