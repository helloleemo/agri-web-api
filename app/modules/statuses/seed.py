
from sqlalchemy.orm import Session
from app.modules.statuses.model import Status

def seed_statuses(db: Session) -> None:
    statuses = [
        {"id": 1, "code": "active", "name": "enabled", "category": "common"},
        {"id": 2, "code": "inactive", "name": "disabled", "category": "common"},
        {"id": 3, "code": "deleted", "name": "deleted", "category": "common"},
        {"id": 4, "code": "pending", "name": "pending", "category": "common"},
    ]

    for item in statuses:
        exists = db.query(Status).filter(Status.code == item["code"]).first()
        if not exists:
            db.add(Status(**item))

    db.commit()