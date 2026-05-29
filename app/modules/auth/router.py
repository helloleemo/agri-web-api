from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.deps import AuthUser, get_auth_context, require_roles
from app.modules.auth.schema import LoginRequest, LoginResponse, RegisterRequest
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.common.response import created, ok
from app.modules.common.schema import ApiResponse
from app.modules.roles.constants import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_MEMBER, ROLE_MEMBER, ROLE_STAFF

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise_error(ErrorCode.USER_INVALID_CREDENTIALS)

    role_code = service.get_role_code(db, user.role_id)
    if role_code is None:
        raise_error(ErrorCode.UNAUTHORIZED, detail="User role is invalid")

    access_token, _ = service.create_access_token({
        "sub": str(user.id),
        "role_code": role_code,
        "email": user.email,
    })

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=ApiResponse[LoginResponse], response_model_exclude_none=True)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = service.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise_error(ErrorCode.USER_INVALID_CREDENTIALS)

    role_code = service.get_role_code(db, user.role_id)
    if role_code is None:
        raise_error(ErrorCode.UNAUTHORIZED, detail="User role is invalid")

    token, expires_in = service.create_access_token({
        "sub": str(user.id),
        "role_code": role_code,
        "email": user.email,
    })

    return ok(
        LoginResponse(
            access_token=token,
            expires_in=expires_in,
            user=AuthUser(
                id=user.id,
                email=user.email,
                user_name=user.user_name,
                role_id=user.role_id,
                role_code=role_code,
            ),
        ),
        "login success",
    )


@router.get(
        "/me", 
        response_model=ApiResponse[AuthUser], 
        response_model_exclude_none=True,
        dependencies=[Depends(require_roles([ROLE_ADMIN, ROLE_STAFF, ROLE_MEMBER, ROLE_CUSTOMER]))],
    )
def me(auth: AuthUser = Depends(get_auth_context)):
    return ok(auth, "profile fetched")


@router.post("/register", response_model=ApiResponse[LoginResponse], status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = service.register_user(db, payload.email, payload.user_name, payload.password, payload.role_code)
    if not user:
        raise_error(ErrorCode.USER_EMAIL_ALREADY_EXISTS)

    role_code = service.get_role_code(db, user.role_id)
    if role_code is None:
        raise_error(ErrorCode.UNAUTHORIZED, detail="User role is invalid")

    token, expires_in = service.create_access_token({
        "sub": str(user.id),
        "role_code": role_code,
        "email": user.email,
    })

    return created(
        LoginResponse(
            access_token=token,
            expires_in=expires_in,
            user=AuthUser(
                id=user.id,
                email=user.email,
                user_name=user.user_name,
                role_id=user.role_id,
                role_code=role_code,
            ),
        ),
        "register success",
    )
