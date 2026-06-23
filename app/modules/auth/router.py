from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.deps import AuthUser, get_auth_context
from app.modules.auth.schema import (
    AuthEmailTemplateResponse,
    AuthEmailTemplateUpdate,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationEmailRequest,
    VerifyEmailRequest,
    VerifyEmailResponse,
)
from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.common.response import created, ok
from app.modules.common.schema import ApiResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise_error(ErrorCode.USER_INVALID_CREDENTIALS)

    role_code = user.role_code
    role_id = service.get_role_id_by_code(db, role_code)
    if role_id is None:
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

    role_code = user.role_code
    role_id = service.get_role_id_by_code(db, role_code)
    if role_id is None:
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
                role_id=role_id,
                role_code=role_code,
            ),
        ),
        "login success",
    )


@router.get("/me", response_model=ApiResponse[AuthUser], response_model_exclude_none=True)
def me(auth: AuthUser = Depends(get_auth_context)):
    return ok(auth, "profile fetched")


@router.post("/register", response_model=ApiResponse[RegisterResponse], status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = service.register_user(db, payload.email, payload.user_name, payload.password, payload.role_code)
    if not user:
        raise_error(ErrorCode.USER_EMAIL_ALREADY_EXISTS)

    verification_token, expires_in = service.create_email_verification_token(user)
    service.send_verification_email(db, user.email, verification_token)

    return created(
        RegisterResponse(email=user.email, verification_expires_in=expires_in),
        "register success, please verify your email",
    )


@router.post("/verify-email", response_model=ApiResponse[VerifyEmailResponse], response_model_exclude_none=True)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    user = service.verify_email_token(db, payload.token)
    return ok(VerifyEmailResponse(email=user.email), "email verified")


@router.post("/resend-verification-email", response_model=ApiResponse[RegisterResponse], response_model_exclude_none=True)
def resend_verification_email(payload: ResendVerificationEmailRequest, db: Session = Depends(get_db)):
    user, expires_in = service.resend_verification_email(db, payload.email)
    if not user:
        return ok(message="If the email exists, a verification email has been sent")
    if expires_in is None:
        return ok(RegisterResponse(email=user.email, verification_expires_in=0), "email already verified")

    return ok(
        RegisterResponse(email=user.email, verification_expires_in=expires_in),
        "verification email sent",
    )


@router.get("/email-templates", response_model=ApiResponse[list[AuthEmailTemplateResponse]], response_model_exclude_none=True)
def get_email_templates(db: Session = Depends(get_db), auth: AuthUser = Depends(get_auth_context)):
    """Get all authentication email templates (admin only)."""
    if auth.role_code not in [1, 2]:  # Admin or Staff
        raise_error(ErrorCode.FORBIDDEN)
    
    from app.modules.auth import crud as auth_crud
    templates = auth_crud.get_all_auth_email_templates(db)
    
    return ok(
        [
            {
                "template_type": t.template_type,
                "subject_template": t.subject_template,
                "body_template": t.body_template,
            }
            for t in templates
        ],
        "email templates fetched",
    )


@router.patch(
    "/email-templates/{template_type}",
    response_model=ApiResponse[AuthEmailTemplateResponse],
    response_model_exclude_none=True,
)
def update_email_template(
    template_type: int,
    payload: AuthEmailTemplateUpdate,
    db: Session = Depends(get_db),
    auth: AuthUser = Depends(get_auth_context),
):
    """Update an authentication email template (admin only)."""
    if auth.role_code not in [1, 2]:  # Admin or Staff
        raise_error(ErrorCode.FORBIDDEN)
    
    from app.modules.auth import crud as auth_crud
    template = auth_crud.update_auth_email_template(db, template_type, payload)
    if not template:
        raise_error(ErrorCode.NOT_FOUND, detail="Failed to update email template")
    
    return ok(
        {
            "template_type": template.template_type,
            "subject_template": template.subject_template,
            "body_template": template.body_template,
        },
        "email template updated",
    )
