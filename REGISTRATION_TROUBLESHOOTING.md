# 註冊錯誤排除指南

## 問題
註冊時出現 `INTERNAL_SERVER_ERROR` 錯誤

## 根本原因
通常由以下原因之一引起：
1. **資料庫未初始化** - 沒有運行 seed 腳本
2. **缺少基本角色數據** - roles 表中沒有 code=3 (customer) 的記錄
3. **用戶創建時出錯** - 數據庫連接問題或約束違反

## 解決步驟

### 1. 初始化資料庫（第一次運行）

```bash
# 進入項目目錄
cd /Users/leemo/Desktop/project/agi-web/agri-api

# 啟用虛擬環境
source venv/bin/activate

# 運行 seed 腳本
python -m app.seed
```

期望輸出：
```
開始 seed...
  [完成] 新增 3 筆 statuses
  [完成] 新增 3 筆 roles
  [完成] 新增 1 筆 users
  [完成] 新增 3 筆 products
Seed 完成！
```

### 2. 確保數據庫連接

檢查 `.env` 文件或環境變數：
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/agri_db
```

確保 PostgreSQL 服務運行中。

### 3. 檢查日誌

改進後的代碼現在會顯示詳細的錯誤信息。運行服務時檢查控制台日誌：

```bash
# 啟動服務
python -m uvicorn app.main:app --reload --log-level debug
```

### 4. 測試註冊

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "user_name": "testuser",
    "password": "securepass123"
  }'
```

成功響應應該是：
```json
{
  "success": true,
  "message": "register success",
  "data": {
    "access_token": "...",
    "expires_in": 3600,
    "user": {
      "id": "...",
      "email": "test@example.com",
      "user_name": "testuser",
      "role_id": "...",
      "role_code": 3
    }
  }
}
```

## 常見錯誤

| 錯誤 | 原因 | 解決方案 |
|------|------|--------|
| `USER_EMAIL_ALREADY_EXISTS` | 郵箱已被註冊 | 使用不同的郵箱 |
| `request failed` + `INTERNAL_SERVER_ERROR` | 資料庫問題或 seed 未運行 | 運行 seed 腳本 |
| 連接超時 | 數據庫不可達 | 檢查 DATABASE_URL 和 PostgreSQL 服務 |

## 改進的代碼變更

已做以下改進：
1. ✅ `create_user()` 現在接受 `status_id` 參數（預設值 1）
2. ✅ `register_user()` 添加了日誌記錄用於調試
3. ✅ 異常處理器現在顯示實際錯誤信息而非通用消息
4. ✅ 添加了詳細的錯誤日誌記錄

## 需要幫助？

檢查這些文件：
- [app/seed.py](app/seed.py) - 數據庫初始化腳本
- [app/modules/auth/service.py](app/modules/auth/service.py) - 認證服務（已改進）
- [app/modules/users/crud.py](app/modules/users/crud.py) - 用戶 CRUD 操作（已改進）
