import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.errors import raise_not_found_unit
from app.modules.common.messages import UnitMessages
from app.modules.common.pagination import Pagination, pagination_dep
from app.modules.common.response import created, deleted, ok
from app.modules.common.schema import ApiResponse
from app.modules.roles.constants import RoleCode
from app.modules.units import service
from app.modules.units.schema import CreateUnit, UnitResponse, UpdateUnit


router = APIRouter(
    prefix='/units',
    tags=['Units'],
)


@router.get(
    '',
    response_model=ApiResponse[list[UnitResponse]],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def list_units(
    pagination: Pagination = Depends(pagination_dep),
    db: Session = Depends(get_db),
):
    units = service.list_units(db)
    return ok(units, UnitMessages.LIST)


@router.get(
    '/{unit_id}',
    response_model=ApiResponse[UnitResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def get_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    unit = service.get_unit(db, unit_id)
    if not unit:
        raise_not_found_unit(str(unit_id))

    return ok(unit, UnitMessages.GET)


@router.post(
    '',
    response_model=ApiResponse[UnitResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def create_unit(payload: CreateUnit, db: Session = Depends(get_db)):
    unit = service.create_unit(db, payload)
    return created(unit, UnitMessages.CREATE)


@router.put(
    '/{unit_id}',
    response_model=ApiResponse[UnitResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def update_unit(unit_id: uuid.UUID, payload: UpdateUnit, db: Session = Depends(get_db)):
    unit = service.update_unit(db, unit_id, payload)
    if not unit:
        raise_not_found_unit(str(unit_id))

    return ok(unit, UnitMessages.UPDATE)


@router.delete(
    '/{unit_id}',
    response_model=ApiResponse[dict[str, str]],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def delete_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)):
    deleted_ok = service.delete_unit(db, unit_id)
    if not deleted_ok:
        raise_not_found_unit(str(unit_id))

    return deleted(str(unit_id), UnitMessages.DELETE)
