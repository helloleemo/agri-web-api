from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.model import Role

def seed_roles(db:Session):
    roles = [
        {"name": "admin", "code": 1},
        {"name": "customer", "code": 2},
    ]

    for item in roles:
        stmt = select(Role).where(Role.code == item["code"])
        exists = db.scalar(stmt)
        if not exists:
            db.add(Role(**item))

    db.commit()