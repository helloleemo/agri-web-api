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
from app.modules.roles.model import Role
from app.modules.statuses.constants import StatusCode
from app.modules.users import crud as users_crud
from app.modules.users.model import User

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "1440"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-env")
FRONTEND_VERIFY_URL = os.getenv("FRONTEND_VERIFY_URL", "http://localhost:5173/verify-email")
MAIL_FROM = os.getenv("MAIL_FROM", "noreply@example.com")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


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
    separator = "&" if "?" in FRONTEND_VERIFY_URL else "?"
    return f"{FRONTEND_VERIFY_URL}{separator}token={token}"


def send_verification_email(email: str, token: str) -> None:
    verification_link = build_verification_link(token)

    if not SMTP_HOST:
        logger.warning("SMTP_HOST is not configured. Verification link for %s: %s", email, verification_link)
        return

    message = EmailMessage()
    message["Subject"] = "Verify your email"
    message["From"] = MAIL_FROM
    message["To"] = email
    message.set_content(
        "Welcome to Agri API.\n\n"
        f"Please verify your email by opening this link:\n{verification_link}\n\n"
        f"This link expires in {EMAIL_VERIFICATION_EXPIRE_MINUTES} minutes."
    )

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        if SMTP_USE_TLS:
            smtp.starttls()
            smtp.ehlo()
        if SMTP_USERNAME:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD or "")
        smtp.send_message(message)


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
    if user.email_verified_at is not None:
        return user, None

    token, expires_in = create_email_verification_token(user)
    send_verification_email(user.email, token)
    return user, expires_in



