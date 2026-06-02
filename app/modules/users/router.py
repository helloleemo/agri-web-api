import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.errors import raise_not_found_user
from app.modules.common.messages import UserMessages
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.users import service
from app.modules.users.schema import UserCreate, UserResponse, UserUpdate
from app.modules.roles.constants import RoleCode

router = APIRouter(
    prefix="/users",
    tags=["Users"],
	dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value, RoleCode.ROLE_MEMBER.value]))],
)

@router.get("", response_model=ApiResponse[list[UserResponse]], response_model_exclude_none=True)
def list_users(
	pagination: Pagination = Depends(pagination_dep),
	db: Session = Depends(get_db),
):
	users = service.list_users(db, skip=pagination.skip, limit=pagination.limit)
	return ok(users, UserMessages.LIST)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse], response_model_exclude_none=True)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
	user = service.get_user_by_id(db, user_id)
	if not user:
		raise_not_found_user(str(user_id))

	return ok(user, UserMessages.GET)


@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
	user = service.create_user(db, payload)
	return created(user, UserMessages.CREATE)


@router.patch("/{user_id}", response_model=ApiResponse[UserResponse], response_model_exclude_none=True)
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: Session = Depends(get_db)):
	user = service.update_user(db, user_id, payload)
	if not user:
		raise_not_found_user(str(user_id))

	return ok(user, UserMessages.UPDATE)


@router.delete("/{user_id}", response_model=ApiResponse[dict[str, str]], response_model_exclude_none=True)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
	is_deleted = service.delete_user(db, user_id)
	if not is_deleted:
		raise_not_found_user(str(user_id))

	return deleted(str(user_id), UserMessages.DELETE)
