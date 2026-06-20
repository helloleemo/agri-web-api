import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.units.model import Unit


def get_unit_by_id(db: Session, unit_id: uuid.UUID) -> Unit | None:
    stmt = select(Unit).where(Unit.id == unit_id)
    return db.scalar(stmt)


def get_unit_by_name(db: Session, name: str) -> Unit | None:
    stmt = select(Unit).where(Unit.name == name)
    return db.scalar(stmt)


def get_units(db: Session) -> list[Unit]:
    stmt = select(Unit).order_by(Unit.name.asc())
    return list(db.scalars(stmt).all())


def create_unit(db: Session, name: str) -> Unit:
    unit = Unit(name=name)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit_id: uuid.UUID, name: str) -> Unit | None:
    unit = get_unit_by_id(db, unit_id)
    if not unit:
        return None

    unit.name = name
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit_id: uuid.UUID) -> bool:
    unit = get_unit_by_id(db, unit_id)
    if not unit:
        return False

    db.delete(unit)
    db.commit()
    return True
