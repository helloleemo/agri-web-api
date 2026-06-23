from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.model import AuthEmailTemplate
from app.modules.auth.schema import AuthEmailTemplateUpdate


def get_auth_email_template(db: Session, template_type: int) -> AuthEmailTemplate | None:
    stmt = select(AuthEmailTemplate).where(AuthEmailTemplate.template_type == template_type)
    return db.scalar(stmt)


def get_all_auth_email_templates(db: Session) -> list[AuthEmailTemplate]:
    stmt = select(AuthEmailTemplate).order_by(AuthEmailTemplate.template_type)
    return db.scalars(stmt).all()


def update_auth_email_template(
    db: Session, template_type: int, data: AuthEmailTemplateUpdate
) -> AuthEmailTemplate | None:
    template = get_auth_email_template(db, template_type)
    if not template:
        # Create if not exists
        template = AuthEmailTemplate(
            template_type=template_type,
            subject_template=data.subject_template,
            body_template=data.body_template,
        )
        db.add(template)
    else:
        if data.subject_template is not None:
            template.subject_template = data.subject_template
        if data.body_template is not None:
            template.body_template = data.body_template

    db.commit()
    db.refresh(template)
    return template
