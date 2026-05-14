from typing import TypeVar

from app.modules.common.schema import ApiResponse

T = TypeVar("T")


def ok(data: T | None = None, message: str = "Success") -> ApiResponse[T | None]:
    return ApiResponse(success=True, message=message, data=data, error=None)


def created(data: T | None = None, message: str = "Created") -> ApiResponse[T | None]:
    return ApiResponse(success=True, message=message, data=data, error=None)


def deleted(resource_id: str, message: str = "deleted") -> ApiResponse[dict[str, str]]:
    return ApiResponse(success=True, message=message, data={"id": resource_id}, error=None)
