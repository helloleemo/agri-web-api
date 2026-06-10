import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.orders.model import Order, OrderItem
from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserUpdate
from app.modules.statuses.constants import StatusCode


def _hash_password(password: str) -> str:
	salt = secrets.token_hex(16)
	digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
	return f"{salt}${digest.hex()}"

def get_user_by_id(db:Session, user_id:uuid.UUID) -> User | None:
	stmt = (
		select(User)
		.where(
			User.id == user_id,
			User.status_code != StatusCode.DELETED.value,
		)
		.options(selectinload(User.orders).selectinload(Order.items).selectinload(OrderItem.product))
		### selectinload
	)

	return db.scalar(stmt)

def get_user_by_email(db:Session, email:str) -> User |None:
	stmt = select(User).where(
		User.email == email,
		User.status_code != StatusCode.DELETED.value,
	)
	return db.scalar(stmt)

def get_users(db: Session, skip: int = 0, limit: int = 10) -> list[User]:
	stmt = (
		select(User)
		.where(User.status_code != StatusCode.DELETED.value)
		.options(selectinload(User.orders).selectinload(Order.items).selectinload(OrderItem.product))
		.offset(skip)
		.limit(limit)
	)
	return list(db.scalars(stmt).all())

def create_user(db: Session, user_create:UserCreate) -> User:
	payload = user_create.model_dump()
	password = payload.pop("password")
	payload["password_hash"] = _hash_password(password)
	if hasattr(payload.get("role_code"), "value"):
		payload["role_code"] = payload["role_code"].value
	payload.setdefault("status_code", StatusCode.ENABLED.value)
	now = datetime.now(timezone.utc)
	payload.setdefault("created_at", now)
	payload.setdefault("updated_at", now)

	new_user = User(**payload)

	db.add(new_user)
	db.commit()
	db.refresh(new_user)
	return new_user


def update_user(db: Session, user_id: uuid.UUID, user_update: UserUpdate) -> User | None:
	user = get_user_by_id(db, user_id)
	if not user:
		return None

	payload = user_update.model_dump(exclude_unset=True)
	password = payload.pop("password", None)
	if password is not None:
		payload["password_hash"] = _hash_password(password)
	if hasattr(payload.get("role_code"), "value"):
		payload["role_code"] = payload["role_code"].value

	for field, value in payload.items():
		setattr(user, field, value)

	db.commit()
	db.refresh(user)
	return user

def delete_user(db: Session, user_id: uuid.UUID) -> None:
	user = get_user_by_id(db, user_id)
	if not user:
		return None

	user.status_code = StatusCode.DELETED.value
	db.commit()
