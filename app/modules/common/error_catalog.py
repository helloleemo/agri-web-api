from dataclasses import dataclass

from app.modules.common.error_code import ErrorCode


@dataclass(frozen=True, slots=True)
class ErrorSpec:
    code: ErrorCode
    http_status: int
    message: str
    detail: str


ERROR_CATALOG: dict[ErrorCode, ErrorSpec] = {
    # Common
    ErrorCode.VALIDATION_ERROR: ErrorSpec(ErrorCode.VALIDATION_ERROR, 422, "validation failed", "Request validation failed"),
    ErrorCode.BAD_REQUEST: ErrorSpec(ErrorCode.BAD_REQUEST, 400, "bad request", "Request is invalid"),
    ErrorCode.UNAUTHORIZED: ErrorSpec(ErrorCode.UNAUTHORIZED, 401, "unauthorized", "Authentication is required"),
    ErrorCode.FORBIDDEN: ErrorSpec(ErrorCode.FORBIDDEN, 403, "forbidden", "You do not have permission"),
    ErrorCode.NOT_FOUND: ErrorSpec(ErrorCode.NOT_FOUND, 404, "not found", "Resource not found"),
    ErrorCode.CONFLICT: ErrorSpec(ErrorCode.CONFLICT, 409, "conflict", "Resource conflict"),
    ErrorCode.INTERNAL_SERVER_ERROR: ErrorSpec(ErrorCode.INTERNAL_SERVER_ERROR, 500, "request failed", "Unexpected server error"),

    # Users
    ErrorCode.USER_NOT_FOUND: ErrorSpec(ErrorCode.USER_NOT_FOUND, 404, "not found", "User not found"),
    ErrorCode.USER_EMAIL_ALREADY_EXISTS: ErrorSpec(ErrorCode.USER_EMAIL_ALREADY_EXISTS, 409, "conflict", "Email already exists"),
    ErrorCode.USER_INVALID_CREDENTIALS: ErrorSpec(ErrorCode.USER_INVALID_CREDENTIALS, 401, "unauthorized", "Invalid email or password"),
    ErrorCode.USER_EMAIL_NOT_VERIFIED: ErrorSpec(ErrorCode.USER_EMAIL_NOT_VERIFIED, 403, "forbidden", "Email address has not been verified"),

    # Products
    ErrorCode.PRODUCT_NOT_FOUND: ErrorSpec(ErrorCode.PRODUCT_NOT_FOUND, 404, "not found", "Product not found"),
    ErrorCode.PRODUCT_SKU_ALREADY_EXISTS: ErrorSpec(ErrorCode.PRODUCT_SKU_ALREADY_EXISTS, 409, "conflict", "SKU already exists"),
    ErrorCode.PRODUCT_OUT_OF_STOCK: ErrorSpec(ErrorCode.PRODUCT_OUT_OF_STOCK, 409, "conflict", "Product is out of stock"),

    # Orders
    ErrorCode.ORDER_NOT_FOUND: ErrorSpec(ErrorCode.ORDER_NOT_FOUND, 404, "not found", "Order not found"),
    ErrorCode.ORDER_INVALID_STATUS: ErrorSpec(ErrorCode.ORDER_INVALID_STATUS, 400, "bad request", "Order status is invalid"),
    ErrorCode.ORDER_ITEM_INVALID: ErrorSpec(ErrorCode.ORDER_ITEM_INVALID, 400, "bad request", "Order item is invalid"),

    # Categories
    ErrorCode.CATEGORY_NOT_FOUND: ErrorSpec(ErrorCode.CATEGORY_NOT_FOUND, 404, "not found", "Category not found"),
    ErrorCode.CATEGORY_NAME_ALREADY_EXISTS: ErrorSpec(ErrorCode.CATEGORY_NAME_ALREADY_EXISTS, 409, "conflict", "Category name already exists"),

    # Images
    ErrorCode.IMAGE_NOT_FOUND: ErrorSpec(ErrorCode.IMAGE_NOT_FOUND, 404, "not found", "Image not found"),
    ErrorCode.IMAGE_INVALID_FORMAT: ErrorSpec(ErrorCode.IMAGE_INVALID_FORMAT, 400, "bad request", "Image format is invalid"),
}


def get_error_spec(code: ErrorCode) -> ErrorSpec:
    return ERROR_CATALOG[code]
