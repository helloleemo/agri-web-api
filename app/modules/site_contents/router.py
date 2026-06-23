from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.deps import require_roles
from app.modules.common.messages import CommonMessages
from app.modules.common.response import ok
from app.modules.common.schema import ApiResponse
from app.modules.roles.constants import RoleCode
from app.modules.site_contents import service
from app.modules.site_contents.schema import (
    PageAssetUploadResponse,
    SiteContentResponse,
    SiteContentUpdate,
)

router = APIRouter(tags=["SiteContents"])


@router.get(
    "/public/site-contents/{page_key}",
    response_model=ApiResponse[SiteContentResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def get_public_site_content(page_key: str, db: Session = Depends(get_db)):
    content = service.get_or_create_site_content(db, page_key)
    return ok(content, CommonMessages.OK)


@router.get(
    "/site-contents/{page_key}",
    response_model=ApiResponse[SiteContentResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def get_site_content(page_key: str, db: Session = Depends(get_db)):
    content = service.get_or_create_site_content(db, page_key)
    return ok(content, CommonMessages.OK)


@router.patch(
    "/site-contents/{page_key}",
    response_model=ApiResponse[SiteContentResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
def update_site_content(page_key: str, payload: SiteContentUpdate, db: Session = Depends(get_db)):
    content = service.update_site_content(db, page_key, payload.content_data)
    return ok(content, CommonMessages.OK)


@router.post(
    "/site-contents/{page_key}/assets",
    response_model=ApiResponse[PageAssetUploadResponse],
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles([RoleCode.ROLE_ADMIN.value, RoleCode.ROLE_STAFF.value]))],
)
async def upload_site_asset(
    page_key: str,
    asset_key: str = Form(...),
    file: UploadFile = File(...),
):
    bucket, object_path, public_url = await service.upload_page_asset(page_key, asset_key, file)
    return ok(
        PageAssetUploadResponse(bucket=bucket, object_path=object_path, public_url=public_url),
        CommonMessages.CREATED,
    )
