# 資料字典與技術規範 (Data Dictionary & Technical Specifications)

## 目次 (Table of Contents)

1. [命名規範](#命名規範)
2. [資料類型對照](#資料類型對照)
3. [欄位標準](#欄位標準)
4. [表格清冊](#表格清冊)
5. [API 回應對應](#api-回應對應)
6. [常數與列舉](#常數與列舉)
7. [效能基準](#效能基準)

---

## 命名規範 (Naming Conventions)

### 表格命名
- **格式**: 小寫英文，複數形式或業務領域名稱
- **例子**:
  - `users` - 用戶表
  - `products` - 產品表
  - `order_items` - 訂單項目表
  - `inventory_balances` - 庫存結餘表

### 欄位命名
- **格式**: 小寫英文，單數形式，使用 snake_case
- **外鍵**: `<表名>_<主鍵名>` (例: `user_id`, `product_id`)
- **布林值**: `is_<描述>` (例: `is_primary`, `is_active`)
- **計數**: `<名詞>_count` (例: `used_count`)
- **時間戳**: `<事件>_at` (例: `created_at`, `verified_at`)
- **例子**:
  - `customer_email` - 客戶郵件
  - `order_no` - 訂單編號
  - `manual_adjustment_amount` - 手動調整金額

### 約束命名
| 類型 | 格式 | 例子 |
|------|------|------|
| 主鍵 | `pk_<表名>` | `pk_users` |
| 外鍵 | `fk_<表名>_<欄位>` | `fk_orders_user_id` |
| 唯一 | `uq_<表名>_<欄位>` | `uq_coupons_code` |
| 檢查 | `ck_<表名>_<描述>` | `ck_products_price_non_negative` |
| 複合索引 | `idx_<表名>_<欄位1>_<欄位2>` | `idx_inventory_ledger_product_unit` |

---

## 資料類型對照 (Data Types)

### PostgreSQL 資料類型

| Python 類型 | SQLAlchemy | PostgreSQL | 說明 | 例子 |
|------------|-----------|-----------|------|------|
| str | String(n) | VARCHAR(n) | 可變長文字 | name VARCHAR(120) |
| str | Text | TEXT | 長文本 | description TEXT |
| int | Integer | INTEGER | 整數 | quantity INTEGER |
| bool | Boolean | BOOLEAN | 布林值 | is_primary BOOLEAN |
| dict | JSONB | JSONB | JSON 二進制 | meta_data JSONB |
| datetime | DateTime(timezone=True) | TIMESTAMP WITH TIME ZONE | 時間戳 | created_at TIMESTAMP |
| UUID | UUID | UUID | 通用唯一識別碼 | id UUID |

### 金額與計量單位

| 欄位名 | 資料類型 | 單位 | 說明 | 例子 |
|--------|---------|------|------|------|
| price | INTEGER | 分 (¥0.01) | 產品價格 | 100 = ¥1.00 |
| amount | INTEGER | 分 (¥0.01) | 訂單金額 | 5999 = ¥59.99 |
| discount_value | INTEGER | 分或% | 折扣值 | 固定額或百分比 |

### 代碼欄位

| 欄位名 | 資料類型 | 範圍 | 說明 |
|--------|---------|------|------|
| code | INTEGER | 1-999 | 狀態/角色/訂單狀態代碼 |
| discount_type | INTEGER | 1-2 | 1=固定金額, 2=百分比 |
| delivery_method | INTEGER | 1-5 | 配送方式代碼 |
| payment_method | INTEGER | 1-5 | 付款方式代碼 |

---

## 欄位標準 (Field Standards)

### 必填 (NOT NULL) 欄位清單

#### users 表
- id, email, user_name, password_hash
- role_code, status_code
- created_at, updated_at

#### products 表
- id, name, price, stock
- category_id, status_code
- created_at, updated_at

#### orders 表
- id, order_no, customer_email
- subtotal_amount, discount_amount, shipping_fee, manual_adjustment_amount, total_amount
- delivery_method, payment_method
- user_id, status_code, order_status_code
- created_at, updated_at

#### order_items 表
- id, order_id, product_id, quantity
- (unit 和 unit_id 可選)

### 可選 (NULLABLE) 欄位清單

#### orders 表
- customer_name, address, coupon_code, memo
- bank_transfer_last5
- orderer_name, orderer_phone, orderer_email, admin_note

#### products 表
- origin, low_stock_threshold, description

#### images 表
- 所有欄位都是必填

---

## 表格清冊 (Table Inventory)

### 核心表格

#### 1. users (9 個欄位)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    user_name VARCHAR(20) NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    role_code INTEGER NOT NULL,
    status_code INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (role_code) REFERENCES roles(code),
    FOREIGN KEY (status_code) REFERENCES statuses(code)
);
```
**典型記錄數**: 100-10,000
**資料大小**: < 1 MB

#### 2. products (11 個欄位)
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    origin VARCHAR(120),
    price INTEGER NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER,
    description TEXT,
    category_id UUID NOT NULL,
    status_code INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (status_code) REFERENCES statuses(code),
    CHECK (price >= 0),
    CHECK (stock >= 0),
    CHECK (low_stock_threshold >= 0)
);
```
**典型記錄數**: 50-5,000
**資料大小**: < 5 MB

#### 3. units (2 個欄位)
```sql
CREATE TABLE units (
    id UUID PRIMARY KEY,
    name VARCHAR(20) UNIQUE NOT NULL
);
```
**典型記錄數**: 5-50
**資料大小**: < 10 KB

#### 4. categories (4 個欄位)
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR(60) UNIQUE NOT NULL,
    meta_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```
**典型記錄數**: 5-100
**資料大小**: < 100 KB

---

### 訂單相關表格

#### 5. orders (19 個欄位)
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    order_no VARCHAR(20) UNIQUE NOT NULL,
    customer_email VARCHAR(120) NOT NULL,
    customer_name VARCHAR(100),
    address VARCHAR(255),
    coupon_code VARCHAR(50),
    subtotal_amount INTEGER NOT NULL DEFAULT 0,
    discount_amount INTEGER NOT NULL DEFAULT 0,
    shipping_fee INTEGER NOT NULL DEFAULT 0,
    manual_adjustment_amount INTEGER NOT NULL DEFAULT 0,
    total_amount INTEGER NOT NULL DEFAULT 0,
    delivery_method INTEGER NOT NULL,
    payment_method INTEGER NOT NULL,
    memo VARCHAR(255),
    bank_transfer_last5 VARCHAR(5),
    orderer_name VARCHAR(100),
    orderer_phone VARCHAR(20),
    orderer_email VARCHAR(120),
    admin_note VARCHAR(500),
    status_code INTEGER NOT NULL,
    order_status_code INTEGER NOT NULL,
    user_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (status_code) REFERENCES statuses(code),
    FOREIGN KEY (order_status_code) REFERENCES order_statuses(code),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```
**典型記錄數**: 1,000-100,000
**資料大小**: 10 MB - 1 GB
**備註**: 最容易增長的表，需要定期歸檔

#### 6. order_items (5 個欄位)
```sql
CREATE TABLE order_items (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    unit_id UUID,
    unit VARCHAR(20),
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    CHECK (quantity >= 1)
);
```
**典型記錄數**: 5,000-500,000
**資料大小**: 資料比例: ~5-10 個 order_items 每個 order

---

### 庫存表格

#### 7. inventory_balances (8 個欄位)
```sql
CREATE TABLE inventory_balances (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    unit_id UUID NOT NULL,
    initial_stock INTEGER NOT NULL DEFAULT 0,
    actual_stock INTEGER NOT NULL DEFAULT 0,
    reserved_stock INTEGER NOT NULL DEFAULT 0,
    manual_adjustment_stock INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    UNIQUE (product_id, unit_id),
    CHECK (initial_stock >= 0),
    CHECK (actual_stock >= 0),
    CHECK (reserved_stock >= 0),
    CHECK (actual_stock >= reserved_stock)
);
```
**典型記錄數**: 50-50,000
**資料大小**: < 10 MB
**重要**: 每個 (product_id, unit_id) 組合一條記錄

#### 8. inventory_ledger (16 個欄位)
```sql
CREATE TABLE inventory_ledger (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    unit_id UUID NOT NULL,
    order_id UUID,
    order_item_id UUID,
    action VARCHAR(32) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    delta_actual INTEGER NOT NULL DEFAULT 0,
    delta_reserved INTEGER NOT NULL DEFAULT 0,
    actual_after INTEGER NOT NULL DEFAULT 0,
    reserved_after INTEGER NOT NULL DEFAULT 0,
    available_after INTEGER NOT NULL DEFAULT 0,
    from_order_status_code INTEGER,
    to_order_status_code INTEGER,
    operator_user_id UUID,
    note VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (order_item_id) REFERENCES order_items(id),
    FOREIGN KEY (operator_user_id) REFERENCES users(id)
);
```
**典型記錄數**: 100,000-1,000,000+
**資料大小**: 100 MB - 5 GB
**備註**: 最快增長的表，需要定期歸檔/分表

---

### 購物車表格

#### 9. carts (2 個欄位)
```sql
CREATE TABLE carts (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```
**典型記錄數**: 100-10,000
**資料大小**: < 1 MB
**注意**: 一個用戶只有一個購物車

#### 10. cart_items (5 個欄位)
```sql
CREATE TABLE cart_items (
    id UUID PRIMARY KEY,
    cart_id UUID NOT NULL,
    product_id UUID NOT NULL,
    unit_id UUID,
    quantity INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (cart_id) REFERENCES carts(id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (unit_id) REFERENCES units(id),
    CHECK (quantity >= 1)
);
```
**典型記錄數**: 500-50,000
**資料大小**: < 5 MB

---

### 配置表格

#### 11. coupons (11 個欄位)
```sql
CREATE TABLE coupons (
    id UUID PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(120) NOT NULL,
    discount_type INTEGER NOT NULL,
    discount_value INTEGER NOT NULL,
    min_order_amount INTEGER,
    max_discount_amount INTEGER,
    usage_limit INTEGER,
    used_count INTEGER NOT NULL DEFAULT 0,
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,
    status_code INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (status_code) REFERENCES statuses(code),
    CHECK (discount_value >= 0),
    CHECK (used_count >= 0)
);
```
**典型記錄數**: 10-1,000
**資料大小**: < 500 KB

#### 12. order_statuses (5 個欄位)
```sql
CREATE TABLE order_statuses (
    id UUID PRIMARY KEY,
    code INTEGER UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    customer_email_subject_template VARCHAR(255),
    customer_email_body_template TEXT,
    admin_email_subject_template VARCHAR(255),
    admin_email_body_template TEXT
);
```
**典型記錄數**: 5-20
**資料大小**: < 100 KB

#### 13. statuses (3 個欄位)
```sql
CREATE TABLE statuses (
    id UUID PRIMARY KEY,
    code INTEGER UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL
);
```
**典型記錄數**: 20-50
**資料大小**: < 50 KB

#### 14. roles (3 個欄位)
```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    code INTEGER UNIQUE NOT NULL,
    name VARCHAR(50) UNIQUE NOT NULL
);
```
**典型記錄數**: 2-10
**資料大小**: < 10 KB

---

### 多媒體與配置表格

#### 15. images (6 個欄位)
```sql
CREATE TABLE images (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL,
    stored_filename VARCHAR(300) NOT NULL,
    file_url VARCHAR(300) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```
**典型記錄數**: 100-10,000
**資料大小**: < 10 MB (只儲存元資料)
**注意**: 實際圖片檔案存儲在對象存儲服務

#### 16. product_units (4 個欄位)
```sql
CREATE TABLE product_units (
    product_id UUID,
    unit_id UUID,
    price INTEGER NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL,
    PRIMARY KEY (product_id, unit_id),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (unit_id) REFERENCES units(id)
);
```
**典型記錄數**: 50-10,000
**資料大小**: < 1 MB

#### 17. site_contents (4 個欄位)
```sql
CREATE TABLE site_contents (
    id UUID PRIMARY KEY,
    page_key VARCHAR(80) UNIQUE NOT NULL,
    content_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```
**典型記錄數**: 10-100
**資料大小**: < 10 MB

---

## API 回應對應 (API Response Mapping)

### User 物件
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "userName": "john_doe",
    "roleCode": 1,
    "statusCode": 1,
    "emailVerifiedAt": "2026-01-01T12:00:00Z",
    "createdAt": "2026-01-01T12:00:00Z",
    "updatedAt": "2026-01-01T12:00:00Z"
}
```

### Product 物件
```json
{
    "id": "uuid",
    "name": "番茄",
    "origin": "台灣",
    "price": 3999,
    "stock": 100,
    "lowStockThreshold": 10,
    "description": "新鮮番茄",
    "categoryId": "uuid",
    "statusCode": 1,
    "createdAt": "2026-01-01T12:00:00Z",
    "updatedAt": "2026-01-01T12:00:00Z"
}
```

### Order 物件
```json
{
    "id": "uuid",
    "orderNo": "ORD-20260101-0001",
    "customerEmail": "customer@example.com",
    "customerName": "Jane Doe",
    "address": "台北市信義區",
    "couponCode": "SUMMER2026",
    "subtotalAmount": 9999,
    "discountAmount": 1000,
    "shippingFee": 500,
    "manualAdjustmentAmount": 0,
    "totalAmount": 9499,
    "deliveryMethod": 1,
    "paymentMethod": 2,
    "memo": "請在下午送達",
    "bankTransferLast5": "12345",
    "ordererName": "Jane Doe",
    "ordererPhone": "0987654321",
    "ordererEmail": "orderer@example.com",
    "adminNote": "VIP 客戶，優先處理",
    "statusCode": 1,
    "orderStatusCode": 1,
    "userId": "uuid",
    "createdAt": "2026-01-01T12:00:00Z",
    "updatedAt": "2026-01-01T12:00:00Z"
}
```

### OrderItem 物件
```json
{
    "id": "uuid",
    "orderId": "uuid",
    "productId": "uuid",
    "unitId": "uuid",
    "unit": "kg",
    "quantity": 5,
    "product": {...},  // 展開 Product 物件
    "unitRef": {...}   // 展開 Unit 物件
}
```

---

## 常數與列舉 (Constants & Enums)

### 訂單狀態代碼 (Order Status Code)
| code | name | 說明 |
|------|------|------|
| 1 | Pending | 待確認 |
| 2 | Confirmed | 已確認 |
| 3 | Shipped | 已出貨 |
| 4 | Delivered | 已交付 |
| 5 | Cancelled | 已取消 |
| 6 | Returned | 已退貨 |

### 用戶狀態代碼 (User Status Code)
| code | name | 說明 |
|------|------|------|
| 1 | Active | 活躍 |
| 0 | Inactive | 停用 |

### 產品狀態代碼 (Product Status Code)
| code | name | 說明 |
|------|------|------|
| 1 | Published | 已發布 |
| 2 | Draft | 草稿 |
| 0 | Archived | 已歸檔 |

### 配送方式代碼 (Delivery Method Code)
| code | name | 說明 |
|------|------|------|
| 1 | Home Delivery | 宅配 |
| 2 | Store Pickup | 超商取貨 |
| 3 | Farm Pickup | 農場自取 |
| 4 | Express | 快遞 |
| 5 | Special | 特殊配送 |

### 付款方式代碼 (Payment Method Code)
| code | name | 說明 |
|------|------|------|
| 1 | Credit Card | 信用卡 |
| 2 | Bank Transfer | 銀行轉帳 |
| 3 | Convenience Store | 超商付款 |
| 4 | Mobile Payment | 行動支付 |
| 5 | COD | 貨到付款 |

### 優惠券折扣類型 (Coupon Discount Type)
| code | name | 說明 |
|------|------|------|
| 1 | Fixed Amount | 固定金額 |
| 2 | Percentage | 百分比 |

### 用戶角色代碼 (User Role Code)
| code | name | 說明 |
|------|------|------|
| 1 | Admin | 管理員 |
| 2 | Customer | 一般客戶 |

### 庫存變動動作 (Inventory Action)
| action | 說明 |
|--------|------|
| `reserve` | 預留庫存 |
| `release` | 取消預留 |
| `fulfill` | 出貨 |
| `return` | 退貨 |
| `adjustment` | 手動調整 |
| `recount` | 盤點 |

---

## 效能基準 (Performance Benchmarks)

### 查詢效能目標

| 查詢類型 | 目標時間 | 索引 |
|---------|--------|------|
| 按 ID 查詢單筆記錄 | < 1 ms | 主鍵 |
| 按外鍵查詢 (1:N) | < 5 ms | 外鍵索引 |
| 複合索引查詢 | < 10 ms | 複合索引 |
| 排序/分頁查詢 | < 50 ms | 相關索引 |
| 全表掃描 | < 500 ms | N/A |

### 表格大小預測

| 表格 | 1年預測 | 3年預測 |
|------|--------|--------|
| orders | 100 MB | 1 GB |
| order_items | 500 MB | 5 GB |
| inventory_ledger | 1 GB | 10 GB |
| products | < 50 MB | < 100 MB |
| users | < 50 MB | < 100 MB |

### 建議分表/分區策略

**inventory_ledger** - 按時間分區 (月度)
- 理由: 快速增長，需要歸檔老舊數據
- 策略: 每月一個分區

**orders** - 按時間分區 (季度)
- 理由: 大量歷史數據
- 策略: 每季一個分區

---

## 備份與恢復策略 (Backup & Recovery)

### 備份頻率

| 備份類型 | 頻率 | 保留期 |
|---------|------|-------|
| 完整備份 | 每日 (午夜) | 30 天 |
| 增量備份 | 每 4 小時 | 7 天 |
| 交易日誌 | 持續 | 30 天 |

### 關鍵表格優先級

| 優先級 | 表格 | 說明 |
|--------|------|------|
| P0 (最高) | users, orders, products | 業務關鍵 |
| P1 | order_items, carts | 重要 |
| P2 | inventory_* | 審計用 |
| P3 | images, site_contents | 可恢復 |

---

## 文件版本

| 版本 | 日期 | 更新內容 |
|------|------|--------|
| 1.0 | 2026-06-24 | 初始版本，包含17個表格 |

---

## 聯絡方式

如有問題或建議，請聯絡資料庫管理員。
