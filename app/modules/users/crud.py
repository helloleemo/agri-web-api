import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.modules.statuses.constants import STATUS_CODE_DELETED, STATUS_CODE_ENABLED
from app.modules.statuses.utils import get_status_id_by_code
from app.modules.users.model import User
from app.modules.users.schema import UserCreate, UserUpdate


def _hash_password(password: str) -> str:
	salt = secrets.token_hex(16)
	digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
	return f"{salt}${digest.hex()}"

def get_user_by_id(db:Session, user_id:uuid.UUID) -> User | None:
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	conditions = [User.id == user_id]
	if deleted_status_id is not None:
		conditions.append(User.status_id != deleted_status_id)

	stmt = select(User).where(
		*conditions,
	)
	return db.scalar(stmt)

def get_user_by_email(db:Session, email:str) -> User |None:
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	conditions = [User.email == email]
	if deleted_status_id is not None:
		conditions.append(User.status_id != deleted_status_id)

	stmt = select(User).where(
		*conditions
	)
	return db.scalar(stmt)

def get_users(db:Session, skip:int = 0, limit:int=10) -> list[User]:
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	conditions = []
	if deleted_status_id is not None:
		conditions.append(User.status_id != deleted_status_id)

	stmt = (
		select(User)
		.where(*conditions)
		.offset(skip)
		.limit(limit)
	)
	return list(db.scalars(stmt).all())

def create_user(db: Session, user_create: UserCreate, status_id: uuid.UUID | None = None) -> User:
	if status_id is None:
		status_id = get_status_id_by_code(db, STATUS_CODE_ENABLED)
		if status_id is None:
			raise ValueError("Enabled status is not configured")

	payload = user_create.model_dump(exclude={"password"})
	payload["password_hash"] = _hash_password(user_create.password)
	payload["status_id"] = status_id
	now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
	payload["created_at"] = now
	payload["updated_at"] = now

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
	deleted_status_id = get_status_id_by_code(db, STATUS_CODE_DELETED)
	if deleted_status_id is None:
		raise ValueError("Deleted status is not configured")

	user.status_id = deleted_status_id
	db.commit()
