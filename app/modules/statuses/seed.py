
from sqlalchemy.orm import Session
from app.modules.statuses.model import Status
from app.modules.statuses.constants import StatusCode


def seed_statuses(db: Session) -> None:
    statuses = [
        {"code": StatusCode.ENABLED, "name": "enabled"},
        {"code": StatusCode.DISABLED, "name": "disabled"},
        {"code": StatusCode.DELETED, "name": "deleted"},
    ]

    for item in statuses:
        exists = db.query(Status).filter(Status.code == item["code"]).first()
        if not exists:
            db.add(Status(**item))
        else:
            exists.name = item["name"]

    db.commit()