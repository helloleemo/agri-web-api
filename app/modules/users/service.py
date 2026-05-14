
import hashlib
import uuid
from sqlalchemy.orm import Session

from app.modules.users import crud
from app.modules.users.schema import UserCreate, UserResponse, UserUpdate

def _verify_password(plain_password: str, password_hash: str) -> bool:
	salt, digest = password_hash.split("$")
	computed_digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
	return computed_digest == digest

# ---------------------------------

def create_user(db: Session, data:UserCreate) -> UserResponse:
	user = crud.create_user(db, data)
	return UserResponse.model_validate(user)


def list_users(db: Session, skip: int = 0, limit: int = 10) -> list[UserResponse]:
	users = crud.get_users(db, skip=skip, limit=limit)
	return [UserResponse.model_validate(user) for user in users]

def get_user_by_id(db: Session, user_id: uuid.UUID) -> UserResponse | None:
	user = crud.get_user_by_id(db, user_id)
	if not user:
		return None
	return UserResponse.model_validate(user)


def update_user(db: Session, user_id: uuid.UUID, data: UserUpdate) -> UserResponse | None:
	user = crud.update_user(db, user_id, data)
	if not user:
		return None
	return UserResponse.model_validate(user)


def authenticate_user(db: Session, email: str, password: str) -> UserResponse | None:
	users = crud.get_users(db, skip=0, limit=1000)
	user = next((u for u in users if u.email == email), None)
	
	if not user or not _verify_password(password, user.password_hash):
		return None
	
	return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
	user = crud.get_user_by_id(db, user_id)
	if not user:
		return False
	
	crud.delete_user(db, user)
	return True