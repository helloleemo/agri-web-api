import uuid
from collections.abc import Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.schema import AuthUser
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.users import crud as users_crud


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_auth_context(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AuthUser:
    payload = service.decode_access_token(token)
    if not payload:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token payload is invalid")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token subject is invalid")

    user = users_crud.get_user_by_id(db, user_uuid)
    if not user:
        raise_error(ErrorCode.UNAUTHORIZED, detail="User not found or inactive")

    role_code = service.get_role_code(db, user.role_id)
    if role_code is None:
        raise_error(ErrorCode.UNAUTHORIZED, detail="User role is invalid")

    return AuthUser(
        id=user.id,
        email=user.email,
        user_name=user.user_name,
        role_id=user.role_id,
        role_code=role_code,
    )


def require_roles(allowed_role_codes: list[int]) -> Callable[..., AuthUser]:
    def checker(auth: AuthUser = Depends(get_auth_context)) -> AuthUser:
        if auth.role_code not in allowed_role_codes:
            raise_error(ErrorCode.FORBIDDEN, detail="Insufficient role permissions")
        return auth

    return checker
