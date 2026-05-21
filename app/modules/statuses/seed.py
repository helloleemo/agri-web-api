
from sqlalchemy.orm import Session
from app.modules.statuses.model import Status


def seed_statuses(db: Session) -> None:
    statuses = [
        {"code": 1, "name": "enabled"},
        {"code": 2, "name": "disabled"},
        {"code": 3, "name": "deleted"},
    ]

    for item in statuses:
        exists = db.query(Status).filter(Status.code == item["code"]).first()
        if not exists:
            db.add(Status(**item))
        else:
            exists.name = item["name"]

    db.commit()