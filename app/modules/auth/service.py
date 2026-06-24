import hashlib
import smtplib
import os
import logging
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.auth.constants import AuthEmailTemplateType
from app.modules.auth import crud as auth_crud
from app.modules.roles.model import Role
from app.modules.statuses.constants import StatusCode
from app.modules.users import crud as users_crud
from app.modules.users.schema import UserUpdate
from app.modules.users.model import User

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "1440"))
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-env")
FRONTEND_VERIFY_URL = os.getenv("FRONTEND_VERIFY_URL", "http://localhost:5173/auth/verify-email")
FRONTEND_RESET_PASSWORD_URL = os.getenv("FRONTEND_RESET_PASSWORD_URL", "http://localhost:5173/auth/reset-password")
MAIL_FROM = os.getenv("MAIL_FROM")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


class _TemplateValues(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def verify_password(plain_password: str, password_hash: str) -> bool:
    salt, digest = password_hash.split("$", maxsplit=1)
    computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return computed == digest

def get_role_code(db: Session, role_id: Any) -> int | None:
    stmt = select(Role.code).where(Role.id == role_id)
    return db.scalar(stmt)


def get_role_id_by_code(db: Session, role_code: int) -> uuid.UUID | None:
    stmt = select(Role.id).where(Role.code == role_code)
    return db.scalar(stmt)


def register_user(db: Session, email: str, user_name: str, password: str, role_code: int) -> User | None:
    if users_crud.get_user_by_email(db, email):
        logger.warning(f"Registration attempt with existing email: {email}")
        return None

    role = db.scalar(select(Role).where(Role.code == role_code))
    if not role:
        logger.error(f"Role (code={role_code}) not found in database. Please run seed script first.")
        return None

    try:
        from app.modules.users.schema import UserCreate
        data = UserCreate(email=email, user_name=user_name, password=password, role_code=role.code)
        return users_crud.create_user(db, data)
    except Exception as e:
        logger.error(f"Error creating user during registration: {e}", exc_info=True)
        db.rollback()
        raise

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = users_crud.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if user.status_code != StatusCode.ENABLED.value:
        raise_error(ErrorCode.UNAUTHORIZED, detail="User account is disabled")
    if user.email_verified_at is None:
        raise_error(ErrorCode.USER_EMAIL_NOT_VERIFIED)
    return user


def create_access_token(data: dict[str, Any]) -> tuple[str, int]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**data, "exp": expires_at}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return token, expires_in

def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def create_email_verification_token(user: User) -> tuple[str, int]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=EMAIL_VERIFICATION_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "type": "verify_email",
        "exp": expires_at,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return token, expires_in


def decode_email_verification_token(token: str) -> dict[str, Any] | None:
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "verify_email":
        return None
    return payload


def build_verification_link(token: str) -> str:
    verify_url = FRONTEND_VERIFY_URL.strip()

    # Normalize to hash-router style path expected by frontend app.
    if "#/" not in verify_url:
        verify_url = verify_url.rstrip("/")
        if verify_url.endswith("/auth/verify-email"):
            verify_url = verify_url[:-len("/auth/verify-email")] + "/#/auth/verify-email"
        else:
            verify_url = verify_url + "/#/auth/verify-email"

    separator = "&" if "?" in verify_url else "?"
    return f"{verify_url}{separator}token={token}"


def send_email(to_email: str, subject: str, body: str) -> None:
    if not SMTP_HOST:
        logger.warning("SMTP_HOST is not configured. Email to %s with subject %s was not sent.", to_email, subject)
        logger.warning("Email body for %s:\n%s", to_email, body)
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = MAIL_FROM
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        if SMTP_USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        if SMTP_USERNAME:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD or "")
        smtp.send_message(message)


DEFAULT_VERIFICATION_EMAIL_SUBJECT = "農產品交易平台 - 驗證您的電子郵件"
DEFAULT_VERIFICATION_EMAIL_BODY = (
    "歡迎使用農產品交易平台。\n\n"
    "請通過打開此連結來驗證您的電子郵件:\n{verification_link}\n\n"
    "如果您無法點擊連結，請將以上網址複製並貼到瀏覽器中。\n\n"
    "如果您沒有註冊過農產品交易平台，請忽略這封郵件。\n\n"
    "若連結失效，您可以在登入頁面點擊「重新發送驗證郵件」來獲取新的驗證連結。\n\n"
    "此連結在 {expires_minutes} 分鐘後過期。"
)

DEFAULT_PASSWORD_RESET_EMAIL_SUBJECT = "農產品交易平台 - 重設您的密碼"
DEFAULT_PASSWORD_RESET_EMAIL_BODY = (
    "您好，\n\n"
    "我們收到一筆重設密碼請求。請點擊以下連結設定新密碼：\n{reset_link}\n\n"
    "若您無法直接點擊連結，請將上述網址複製到瀏覽器開啟。\n\n"
    "如果這不是您本人操作，請忽略此信件。\n\n"
    "此連結在 {expires_minutes} 分鐘後過期。"
)


def send_verification_email(db: Session, email: str, token: str) -> None:
    verification_link = build_verification_link(token)
    template = auth_crud.get_auth_email_template(db, AuthEmailTemplateType.REGISTRATION_VERIFICATION.value)

    subject_template = template.subject_template if template and template.subject_template is not None else DEFAULT_VERIFICATION_EMAIL_SUBJECT
    body_template = template.body_template if template and template.body_template is not None else DEFAULT_VERIFICATION_EMAIL_BODY

    template_values = _TemplateValues(
        verification_link=verification_link,
        expires_minutes=EMAIL_VERIFICATION_EXPIRE_MINUTES,
        token=token,
        email=email,
    )
    try:
        subject = subject_template.format_map(template_values)
        body = body_template.format_map(template_values)
    except Exception as exc:
        logger.warning("Failed to render verification template, fallback to raw template: %s", exc)
        subject = subject_template
        body = body_template

    send_email(
        email,
        subject,
        body,
    )


def verify_email_token(db: Session, token: str) -> User:
    payload = decode_email_verification_token(token)
    if not payload:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Invalid or expired email verification token")

    user_id = payload.get("sub")
    if not user_id:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token subject is invalid")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token subject is invalid")

    user = users_crud.get_user_by_id(db, user_uuid)
    if not user:
        raise_error(ErrorCode.USER_NOT_FOUND)

    if user.email != payload.get("email"):
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token email does not match user")

    if user.email_verified_at is None:
        user = users_crud.mark_email_verified(db, user)

    return user


def resend_verification_email(db: Session, email: str) -> tuple[User | None, int | None]:
    user = users_crud.get_user_by_email(db, email)
    if not user or user.status_code == StatusCode.DELETED.value:
        return None, None

    # Re-sending verification should force verification flow again.
    if user.email_verified_at is not None:
        user = users_crud.mark_email_unverified(db, user)

    token, expires_in = create_email_verification_token(user)
    send_verification_email(db, user.email, token)
    return user, expires_in


def create_password_reset_token(user: User) -> tuple[str, int]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "type": "reset_password",
        "exp": expires_at,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return token, expires_in


def decode_password_reset_token(token: str) -> dict[str, Any] | None:
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "reset_password":
        return None
    return payload


def build_password_reset_link(token: str) -> str:
    reset_url = FRONTEND_RESET_PASSWORD_URL.strip()

    if "#/" not in reset_url:
        reset_url = reset_url.rstrip("/")
        if reset_url.endswith("/auth/reset-password"):
            reset_url = reset_url[:-len("/auth/reset-password")] + "/#/auth/reset-password"
        else:
            reset_url = reset_url + "/#/auth/reset-password"

    separator = "&" if "?" in reset_url else "?"
    return f"{reset_url}{separator}token={token}"


def send_password_reset_email(db: Session, email: str, token: str) -> None:
    reset_link = build_password_reset_link(token)
    template = auth_crud.get_auth_email_template(db, AuthEmailTemplateType.PASSWORD_RESET.value)

    subject_template = template.subject_template if template and template.subject_template is not None else DEFAULT_PASSWORD_RESET_EMAIL_SUBJECT
    body_template = template.body_template if template and template.body_template is not None else DEFAULT_PASSWORD_RESET_EMAIL_BODY

    template_values = _TemplateValues(
        reset_link=reset_link,
        expires_minutes=PASSWORD_RESET_EXPIRE_MINUTES,
        token=token,
        email=email,
    )

    try:
        subject = subject_template.format_map(template_values)
        body = body_template.format_map(template_values)
    except Exception as exc:
        logger.warning("Failed to render password reset template, fallback to raw template: %s", exc)
        subject = subject_template
        body = body_template

    send_email(email, subject, body)


def request_password_reset(db: Session, email: str) -> None:
    user = users_crud.get_user_by_email(db, email)
    if not user or user.status_code == StatusCode.DELETED.value:
        return

    token, _ = create_password_reset_token(user)
    send_password_reset_email(db, user.email, token)


def reset_password_with_token(db: Session, token: str, new_password: str) -> User:
    payload = decode_password_reset_token(token)
    if not payload:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Invalid or expired password reset token")

    user_id = payload.get("sub")
    if not user_id:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token subject is invalid")

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token subject is invalid")

    user = users_crud.get_user_by_id(db, user_uuid)
    if not user:
        raise_error(ErrorCode.USER_NOT_FOUND)

    if user.email != payload.get("email"):
        raise_error(ErrorCode.UNAUTHORIZED, detail="Token email does not match user")

    users_crud.update_user(db, user_uuid, UserUpdate(password=new_password))
    return user





def get_all_auth_email_templates_response(db: Session) -> list:
    """Get all authentication email templates."""
    from app.modules.auth import crud as auth_crud
    from app.modules.auth.schema import AuthEmailTemplateResponse
    
    templates = auth_crud.get_all_auth_email_templates(db)
    return [
        AuthEmailTemplateResponse(
            template_type=t.template_type,
            subject_template=t.subject_template,
            body_template=t.body_template,
        )
        for t in templates
    ]


def update_auth_email_template_service(
    db: Session, template_type: int, data
) -> dict:
    """Update or create an authentication email template."""
    from app.modules.auth import crud as auth_crud
    
    template = auth_crud.update_auth_email_template(db, template_type, data)
    if not template:
        raise_error(ErrorCode.NOT_FOUND, detail="Failed to update email template")
    
    return {
        "template_type": template.template_type,
        "subject_template": template.subject_template,
        "body_template": template.body_template,
    }
