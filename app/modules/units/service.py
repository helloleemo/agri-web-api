from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session

from app.modules.common.error_code import ErrorCode
from app.modules.common.errors import raise_error
from app.modules.units import crud
from app.modules.units.model import Unit
from app.modules.units.schema import CreateUnit, UnitResponse, UpdateUnit


def _to_unit_response(unit: Unit) -> UnitResponse:
    created_at = getattr(unit, 'created_at', None) or datetime.now(timezone.utc)
    updated_at = getattr(unit, 'updated_at', None) or created_at

    return UnitResponse(
        id=unit.id,
        name=unit.name,
        created_at=created_at,
        updated_at=updated_at,
    )


def list_units(db: Session) -> list[UnitResponse]:
    units = crud.get_units(db)
    return [_to_unit_response(unit) for unit in units]


def get_unit(db: Session, unit_id: uuid.UUID) -> UnitResponse | None:
    unit = crud.get_unit_by_id(db, unit_id)
    if not unit:
        return None
    return _to_unit_response(unit)


def create_unit(db: Session, data: CreateUnit) -> UnitResponse:
    name = data.name.strip()
    if not name:
        raise_error(ErrorCode.BAD_REQUEST, detail='Unit name is required')

    existing = crud.get_unit_by_name(db, name)
    if existing:
        raise_error(ErrorCode.UNIT_NAME_ALREADY_EXISTS, detail=f'Unit name already exists: {name}')

    unit = crud.create_unit(db, name)
    return _to_unit_response(unit)


def update_unit(db: Session, unit_id: uuid.UUID, data: UpdateUnit) -> UnitResponse | None:
    name = data.name.strip()
    if not name:
        raise_error(ErrorCode.BAD_REQUEST, detail='Unit name is required')

    existing = crud.get_unit_by_name(db, name)
    if existing and existing.id != unit_id:
        raise_error(ErrorCode.UNIT_NAME_ALREADY_EXISTS, detail=f'Unit name already exists: {name}')

    updated = crud.update_unit(db, unit_id, name)
    if not updated:
        return None

    return _to_unit_response(updated)


def delete_unit(db: Session, unit_id: uuid.UUID) -> bool:
    unit = crud.get_unit_by_id(db, unit_id)
    if not unit:
        return False

    if unit.product_units:
        raise_error(ErrorCode.BAD_REQUEST, detail='Unit is in use by products and cannot be deleted')

    return crud.delete_unit(db, unit_id)
