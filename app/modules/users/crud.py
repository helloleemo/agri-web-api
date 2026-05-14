import hashlib
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserUpdate


def _hash_password(password: str) -> str:
	salt = secrets.token_hex(16)
	digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
	return f"{salt}${digest.hex()}"

def get_user_by_id(db:Session, user_id:uuid.UUID) -> User | None:
	stmt = select(User).where(
		User.status_id  != 3,
		User.id == user_id,
	)
	return db.scalar(stmt)

def get_users(db:Session, skip:int = 0, limit:int=10) -> list[User]:
	stmt = (
		select(User)
		.where(User.status_id != 3)
		.offset(skip)
		.limit(limit)
	)
	return list(db.scalars(stmt).all())

def create_user(db: Session, user_create: UserCreate) -> User:
	payload = user_create.model_dump(exclude={"password"})
	payload["password_hash"] = _hash_password(user_create.password)

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

	for field, value in payload.items():
		setattr(user, field, value)

	db.commit()
	db.refresh(user)
	return user


def delete_user(db: Session, user: User) -> None:
	user.status_id = 3
	db.commit()
