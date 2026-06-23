from __future__ import annotations

import io
import os
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image as PILImage
from PIL import ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.supabase import supabase_client
from app.modules.site_contents import crud
from app.modules.site_contents.schema import SiteContentResponse

ALLOWED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
WEBP_QUALITY = 85
PAGE_ASSET_BUCKET = "pages"
DEFAULT_HOME_CONTENT = {
    "hero": {
        "title": "農場直送的真實新鮮",
        "description": "精選在地小農合作，當日採收、當日出貨。每一口都來自看得見的土地，為你保留蔬果最純粹的味道。",
        "button_text": "立即預訂",
        "button_link": "/mekarang/products",
        "image_url": "https://images.unsplash.com/photo-1471194402529-8e0f5a675de6?auto=format&fit=crop&w=1800&q=80",
    },
    "showcase_blocks": [
        {
            "title": "友善耕作，季節直送",
            "description": "挑選當季最鮮甜的蔬果，由合作農場每日採收。從田間到餐桌，每一份都保留自然風味與安心履歷。",
            "image_url": "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1800&q=80",
        },
        {
            "title": "品質把關，全程透明",
            "description": "每批產品皆經過分級與包裝檢驗，提供清楚來源與保存建議，讓你可以輕鬆選購、放心食用。",
            "image_url": "https://picsum.photos/id/684/600/400?auto=format&fit=crop&w=1800&q=80",
        },
    ],
    "flow": {
        "title": "從下單到餐桌的三步驟",
        "items": [
            {"title": "訂購", "description": "線上快速選購，依需求挑選蔬果組合與配送時段。"},
            {"title": "打包", "description": "採收後即刻分類與低溫包裝，完整保留新鮮口感。"},
            {"title": "到府", "description": "冷鏈配送準時送達，讓每日料理都能輕鬆上桌。"},
        ],
    },
    "bottom_cta": {
        "title": "現在訂購，享受當季直送",
        "description": "每週更新當季蔬果清單，提供單次購買與定期配送。把採收時刻的清甜，準時送到你的廚房。",
        "button_text": "立即開始",
        "button_link": "/mekarang/products",
        "image_url": "https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=1800&q=80",
    },
    "mekarang": {
        "banner_image_url": "https://images.unsplash.com/photo-1502741338009-cac2772e18bc?auto=format&fit=crop&w=1800&q=80",
    },
    "orders_query": {
        "description": "輸入你的訂單編號與 Email，立即查看付款狀態、配送進度與收件資訊。若你剛完成下單，也可以在這裡快速追蹤最新處理狀態。",
        "image_url": "https://images.unsplash.com/photo-1471194402529-8e0f5a675de6?auto=format&fit=crop&w=1800&q=80",
    },
    "footer": {
        "title": "與我們保持聯繫",
        "button_text": "開始選購",
        "description": "分享料理靈感、農場日常與最新檔期。追蹤我們，第一時間收到新品上市與優惠資訊。",
        "social_links": {
            "facebook": "",
            "instagram": "",
            "youtube": "",
        },
    },
}


def _sanitize_segment(value: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip())
    sanitized = sanitized.strip("-").lower()
    return sanitized or "default"


def get_or_create_site_content(db: Session, page_key: str) -> SiteContentResponse:
    site_content = crud.get_site_content_by_page_key(db, page_key)
    if site_content:
        return SiteContentResponse.model_validate(site_content)

    fallback = DEFAULT_HOME_CONTENT if page_key == "home" else {}
    created = crud.upsert_site_content_by_page_key(db, page_key=page_key, content_data=fallback)
    return SiteContentResponse.model_validate(created)


def update_site_content(db: Session, page_key: str, content_data: dict) -> SiteContentResponse:
    updated = crud.upsert_site_content_by_page_key(db, page_key=page_key, content_data=content_data)
    return SiteContentResponse.model_validate(updated)


async def upload_page_asset(page_key: str, asset_key: str, file: UploadFile) -> tuple[str, str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="file name is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="unsupported image file type")

    try:
        raw_bytes = await file.read()
        with PILImage.open(io.BytesIO(raw_bytes)) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in {"RGB", "RGBA"}:
                img = img.convert("RGBA")
            output = io.BytesIO()
            img.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)
            output.seek(0)
            image_bytes = output.read()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="invalid image file")

    safe_page_key = _sanitize_segment(page_key)
    safe_asset_key = _sanitize_segment(asset_key)
    stored_filename = f"{uuid.uuid4()}.webp"
    object_path = f"{safe_page_key}/{safe_asset_key}/{stored_filename}"

    supabase_client.storage.from_(PAGE_ASSET_BUCKET).upload(  # type: ignore[union-attr]
        path=object_path,
        file=image_bytes,
        file_options={
            "content-type": "image/webp",
            "upsert": "false",
        },
    )

    public_url = (
        f"{os.getenv('SUPABASE_URL')}"
        f"/storage/v1/object/public/"
        f"{PAGE_ASSET_BUCKET}/{object_path}"
    )
    return PAGE_ASSET_BUCKET, object_path, public_url
