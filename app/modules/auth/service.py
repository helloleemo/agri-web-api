import hashlib
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.constants import ROLE_CUSTOMER
from app.modules.roles.model import Role
from app.modules.users import crud as users_crud
from app.modules.users.model import User

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-env")


def verify_password(plain_password: str, password_hash: str) -> bool:
    salt, digest = password_hash.split("$", maxsplit=1)
    computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return computed == digest

def get_role_code(db: Session, role_id: Any) -> int | None:
    stmt = select(Role.code).where(Role.id == role_id)
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
        data = UserCreate(email=email, user_name=user_name, password=password, role_id=role.id)
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



