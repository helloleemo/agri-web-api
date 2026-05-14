from typing import Generic, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class ErrorPayload(BaseModel):
    code: str
    detail: str

class ApiResponse(GenericModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None
    error: ErrorPayload | None = None