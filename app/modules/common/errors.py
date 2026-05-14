class AppError(Exception):
    def __init__(self, status_code: int, code: str, detail: str, message: str = "request failed"):
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.message = message
        super().__init__(detail)

def raise_not_found(code: str = "NOT_FOUND", detail: str = "Resource not found") -> None:
    raise AppError(status_code=404, code=code, detail=detail, message="not found")