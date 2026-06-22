from typing import TypeVar
import uuid

from app.modules.common.messages import CommonMessages
from app.modules.common.schema import ApiResponse

T = TypeVar("T")


def ok(data: T | None = None, message: str = CommonMessages.OK) -> ApiResponse[T | None]:
    return ApiResponse(success=True, message=message, data=data)


def created(data: T | None = None, message: str = CommonMessages.CREATED) -> ApiResponse[T | None]:
    return ApiResponse(success=True, message=message, data=data)


def deleted(resource_id: str | uuid.UUID | int, message: str = CommonMessages.DELETED) -> ApiResponse[dict[str, str]]:
    return ApiResponse(success=True, message=message, data={"id": resource_id})
