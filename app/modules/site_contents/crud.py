from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.site_contents.model import SiteContent


def get_site_content_by_page_key(db: Session, page_key: str) -> SiteContent | None:
    stmt = select(SiteContent).where(SiteContent.page_key == page_key)
    return db.scalar(stmt)


def upsert_site_content_by_page_key(db: Session, page_key: str, content_data: dict) -> SiteContent:
    site_content = get_site_content_by_page_key(db, page_key)
    if not site_content:
        site_content = SiteContent(page_key=page_key, content_data=content_data)
        db.add(site_content)
    else:
        site_content.content_data = content_data

    db.commit()
    db.refresh(site_content)
    return site_content
