import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.errors import raise_not_found_user
from app.modules.common.messages import UserMessages
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.roles.constants import ROLE_ADMIN
from app.modules.users import service
from app.modules.users.schema import UserCreate, UserResponse, UserUpdate


router = APIRouter(
    prefix="/users",
    tags=["Users"],
	dependencies=[Depends(require_roles([ROLE_ADMIN]))],
)

@router.get("", response_model=ApiResponse[list[UserResponse]], response_model_exclude_none=True)
def list_users(
	skip: int = Query(0, ge=0),
	limit: int = Query(10, ge=1),
	db: Session = Depends(get_db),
):
	users = service.list_users(db, skip=skip, limit=limit)
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
