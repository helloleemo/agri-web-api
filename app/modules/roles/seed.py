from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.constants import ROLE_ADMIN,ROLE_MEMBER, ROLE_CUSTOMER, ROLE_STAFF
from app.modules.roles.model import Role

def seed_roles(db:Session):
    roles = [
        {"name": "admin", "code": ROLE_ADMIN},
        {"name": "staff", "code": ROLE_STAFF},
        {"name": "member", "code": ROLE_MEMBER},
        {"name": "customer", "code": ROLE_CUSTOMER},
    ]

    for item in roles:
        stmt = select(Role).where(Role.code == item["code"])
        exists = db.scalar(stmt)
        if not exists:
            db.add(Role(**item))

    db.commit()