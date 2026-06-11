
import hashlib
import uuid
from sqlalchemy.orm import Session

from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.roles.constants import RoleCode
from app.modules.statuses.constants import StatusCode
from app.modules.users import crud
from app.modules.users.model import User
from app.modules.users.schema import (
	ChangePasswordRequest,
	UserCreate,
	UserOrderItemResponse,
	UserOrderResponse,
	UserResponse,
	UserUpdate,
)

def _verify_password(plain_password: str, password_hash: str) -> bool:
	salt, digest = password_hash.split("$")
	computed_digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
	return computed_digest == digest


def _to_user_response(db: Session, user: User) -> UserResponse:
	orders = [
		UserOrderResponse(
			order_id=order.id,
			items=[
				UserOrderItemResponse(
					product_id=item.product_id,
					product_name=item.product.name if item.product else None,
					quantity=item.quantity,
				)
				for item in order.items
			],
		)
		for order in user.orders
	]

	return UserResponse(
		id=user.id,
		email=user.email,
		user_name=user.user_name,
		role_code=RoleCode(user.role_code),
		status_code=StatusCode(user.status_code),
		orders=orders,
		created_at= user.created_at,
		updated_at=user.updated_at
	)


def create_user(db: Session, data:UserCreate) -> UserResponse:
	user = crud.create_user(db, data)
	return _to_user_response(db, user)


def list_users(db: Session, skip: int = 0, limit: int = 10) -> list[UserResponse]:
	users = crud.get_users(db, skip=skip, limit=limit)
	return [_to_user_response(db, user) for user in users]

def get_user_by_id(db: Session, user_id: uuid.UUID) -> UserResponse | None:
	user = crud.get_user_by_id(db, user_id)
	if not user:
		return None
	return _to_user_response(db, user)


def update_user(db: Session, user_id: uuid.UUID, data: UserUpdate) -> UserResponse | None:
	updated = crud.update_user(db, user_id, data)
	if not updated:
		return None
	return _to_user_response(db, updated)


def authenticate_user(db: Session, email: str, password: str) -> UserResponse | None:
	user = crud.get_user_by_email(db, email)
	
	if not user or not _verify_password(password, user.password_hash):
		return None
	
	return _to_user_response(db, user)


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
	user = crud.get_user_by_id(db, user_id)
	if user is None:
		return False
	
	crud.delete_user(db, user.id)
	return True


def change_password(db: Session, user_id: uuid.UUID, payload: ChangePasswordRequest) -> bool:
	user = crud.get_user_by_id(db, user_id)
	if not user:
		return False

	if not _verify_password(payload.current_password, user.password_hash):
		raise_error(ErrorCode.USER_INVALID_CREDENTIALS, detail="Current password is incorrect")

	if payload.current_password == payload.new_password:
		raise_error(ErrorCode.BAD_REQUEST, detail="New password must be different from current password")

	crud.update_user(db, user_id, UserUpdate(password=payload.new_password))
	return True