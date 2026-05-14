import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.common.schema import ApiResponse
from app.modules.users import service
from app.modules.users.schema import UserCreate, UserResponse, UserUpdate


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=ApiResponse[list[UserResponse]])
def list_users(
	skip: int = Query(0, ge=0),
	limit: int = Query(10, ge=1),
	db: Session = Depends(get_db),
):
	users = service.list_users(db, skip=skip, limit=limit)
	return ApiResponse[list[UserResponse]](
		success=True,
		message="users fetched",
		data=users,
	)


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
	user = service.get_user_by_id(db, user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

	return ApiResponse[UserResponse](
		success=True,
		message="user fetched",
		data=user,
	)


@router.post("", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
	user = service.create_user(db, payload)
	return ApiResponse[UserResponse](
		success=True,
		message="user created",
		data=user,
	)


@router.patch("/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(user_id: uuid.UUID, payload: UserUpdate, db: Session = Depends(get_db)):
	user = service.update_user(db, user_id, payload)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

	return ApiResponse[UserResponse](
		success=True,
		message="user updated",
		data=user,
	)


@router.delete("/{user_id}", response_model=ApiResponse[dict[str, str]])
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
	deleted = service.delete_user(db, user_id)
	if not deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

	return ApiResponse[dict[str, str]](
		success=True,
		message="user deleted",
		data={"id": str(user_id)},
	)
