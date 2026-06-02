from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.constants import RoleCode
from app.modules.roles.model import Role

def seed_roles(db:Session):
    roles = [
        {"name": "admin", "code": RoleCode.ROLE_ADMIN},
        {"name": "staff", "code": RoleCode.ROLE_STAFF},
        {"name": "member", "code": RoleCode.ROLE_MEMBER},
    ]

    for item in roles:
        stmt = select(Role).where(Role.code == item["code"])
        exists = db.scalar(stmt)
        if not exists:
            db.add(Role(**item))

    db.commit()