# Agri API

農產品直銷平台後端服務。基於 FastAPI + SQLAlchemy + PostgreSQL 構建。

## 快速開始

### 環境要求
- Python 3.12+
- PostgreSQL 12+
- 虛擬環境（.venv）

### 1. 安裝依賴

```bash
cd agri-api
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 2. 環境配置

複製 `.env.example` 為 `.env`，並填入以下必需變數：

```bash
cp .env.example .env
```

**關鍵配置項**：
- `DATABASE_URL`: PostgreSQL 連接字串
- `SUPABASE_URL`: Supabase 項目 URL
- `SUPABASE_KEY`: Supabase API Key
- `JWT_SECRET`: JWT 簽名密鑰

### 3. 資料庫遷移

使用項目虛擬環境執行遷移（**重要：不要用系統 alembic**）：

```bash
./.venv/bin/python -m alembic upgrade head
```

檢查當前遷移狀態：
```bash
./.venv/bin/python -m alembic current
```

查看遷移歷史：
```bash
./.venv/bin/python -m alembic history --indicate-current
```

### 4. 啟動服務

```bash
python app/main.py
```

或使用 uvicorn 指定埠口：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服務預設運行在 `http://localhost:8000`

## API 文件

啟動後訪問：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 核心模組

- **auth**: 認證與授權（登入、註冊、Email 驗證）
- **users**: 使用者管理
- **products**: 產品管理
- **categories**: 商品分類
- **units**: 計量單位
- **inventories**: 庫存與進出賬
- **orders**: 訂單管理
- **coupons**: 優惠券
- **site_contents**: 頁面內容管理（首頁、產品頁、訂單查詢頁）
- **images**: 圖片上傳與管理

## 頁面內容管理

首頁及相關頁面的文字、圖片、按鈕等可通過 CMS 管理：

**API 端點**：
- `GET /public/site-contents/{page_key}` - 獲取公開內容（首頁等）
- `GET /site-contents/{page_key}` - 獲取內容（需認證）
- `PATCH /site-contents/{page_key}` - 更新內容（需管理員權限）
- `POST /site-contents/{page_key}/assets` - 上傳頁面資源圖片

**支持的 page_key**：
- `home` - 首頁內容

內容以 JSON 格式存儲，包含 hero、showcase、flow、bottom_cta、mekarang、orders_query、footer 等段落。

圖片自動上傳至 Supabase `pages` bucket 並轉換為 WebP 格式。

## 圖片上傳

商品圖片上傳至 Supabase `products` bucket：
- `POST /images/batch` - 批量上傳商品圖片
- 自動轉換為 WebP 格式
- 自動清理舊圖

頁面內容圖片上傳至 Supabase `pages` bucket：
- `POST /site-contents/{page_key}/assets` - 上傳頁面資源圖片

## 測試

運行測試套件：
```bash
pytest
```

## 常見問題

### Alembic 遷移失敗
- 確保使用項目 .venv 執行：`./.venv/bin/python -m alembic ...`
- 檢查 `.env` 中 DATABASE_URL 是否正確
- 驗證 PostgreSQL 連接狀態

### 圖片上傳失敗
- 檢查 Supabase 憑證是否配置正確
- 確保 bucket (`products`, `pages`) 存在且權限正確
- 驗證上傳文件格式（PNG/JPEG/WebP/GIF）

## 其他資源

- 訂單狀態管理：[order-number.md](../agri-web/agri-api/app/modules/orders/README.md)
- 庫存管理：參考 [inventory.md](../memories/repo/inventory.md)
