# 📚 資料庫文件索引 (Database Documentation Index)

**建立日期**: 2026-06-24  
**文件位置**: `/agri-api/` 根目錄  
**格式**: 完整的技術文件集合

---

## 📖 文件清單

### 🔧 核心文件 (4 份)

#### 1. **DATABASE_SCHEMA.md** - 完整資料庫架構文檔
- **大小**: ~400+ 行
- **閱讀時間**: 30-45 分鐘
- **適用**: 架構師、DBA、後端開發者

**主要內容**:
- ✅ 17 個表格的完整規範
- ✅ 實體關係圖 (Mermaid)
- ✅ 表格詳細說明與約束條件
- ✅ 關鍵設計模式說明
- ✅ 資料完整性約束
- ✅ 索引策略與效能優化
- ✅ 安全性考慮
- ✅ 查詢範例與最佳實踐

**何時查看**:
- 設計新功能或修改架構
- 進行資料庫遷移
- 理解複雜的業務邏輯

---

#### 2. **ER_DIAGRAMS.md** - 實體關係圖與流程圖
- **大小**: ~250+ 行
- **閱讀時間**: 15-20 分鐘
- **適用**: 所有開發人員、業務分析師

**主要內容**:
- ✅ 簡化的 ER 圖 (Mermaid)
- ✅ 表格分層關係圖
- ✅ 資料流向序列圖
- ✅ 庫存管理流程圖
- ✅ 訂單狀態流程圖
- ✅ 使用者權限關係圖
- ✅ 產品與庫存關係圖
- ✅ 快速外鍵參考表

**何時查看**:
- 快速理解表格關係
- 會議中展示架構
- 理解業務流程
- 新員工培訓

---

#### 3. **DATA_DICTIONARY.md** - 完整資料字典與技術規範
- **大小**: ~450+ 行
- **閱讀時間**: 45-60 分鐘
- **適用**: DBA、資料分析師、後端開發者

**主要內容**:
- ✅ 命名規範 (表格、欄位、約束)
- ✅ 資料類型對照表
- ✅ 欄位標準與必填規則
- ✅ 17 個表格的 SQL 定義
- ✅ API 回應對應格式
- ✅ 常數與列舉 (30+ 個代碼表)
- ✅ 效能基準與分表策略
- ✅ 備份與恢復策略

**何時查看**:
- 編寫 SQL 查詢或儲存程序
- 設計 API 回應格式
- 進行資料驗證或轉換
- 理解代碼定義

---

#### 4. **QUICK_REFERENCE.md** - 快速參考指南
- **大小**: ~350+ 行
- **閱讀時間**: 5-10 分鐘
- **適用**: 開發人員、測試人員、支援人員

**主要內容**:
- ✅ 17 個表格的速查表 (簡潔版)
- ✅ 代碼速查表 (30+ 個常用代碼)
- ✅ 5 個常用查詢範例
- ✅ 效能提示 (做/不做)
- ✅ 重要提醒 (金額、時區、級聯刪除)
- ✅ 常見錯誤警告

**何時查看**:
- 快速查詢表格結構
- 查找代碼定義
- 日常開發參考
- 寫簡單查詢

---

## 🎯 快速導航表

| 我想... | 查看文件 | 章節 |
|--------|---------|------|
| 了解完整架構 | DATABASE_SCHEMA.md | 開頭的「概述」 |
| 查看表格關係圖 | ER_DIAGRAMS.md | 「簡化的實體關係圖」 |
| 理解訂單流程 | ER_DIAGRAMS.md | 「訂單狀態流程圖」 |
| 理解庫存管理 | ER_DIAGRAMS.md | 「庫存管理流程圖」 |
| 查詢表格結構 | DATA_DICTIONARY.md | 「表格清冊」 |
| 了解金額儲存 | DATA_DICTIONARY.md | 「資料類型對照」 |
| 查找訂單狀態代碼 | QUICK_REFERENCE.md | 「代碼速查表」 |
| 寫一個查詢 | QUICK_REFERENCE.md | 「常用查詢」 |
| 快速查詢字段 | QUICK_REFERENCE.md | 「表格速查表」 |

---

## 📊 資料庫總覽

### 17 個表格分類

```
核心表格 (3)
├── users           - 用戶帳戶認證
├── products        - 農產品資訊
└── categories      - 產品分類

訂單系統 (2)
├── orders          - 客戶訂單 ⚠️ 最容易增長
└── order_items     - 訂單項目

庫存管理 (2)
├── inventory_balances  - 庫存結餘 (實時)
└── inventory_ledger    - 庫存日誌 ⚠️ 最快增長

購物車 (2)
├── carts           - 用戶購物車
└── cart_items      - 購物車項目

配置系統 (5)
├── units           - 計量單位
├── coupons         - 優惠券
├── order_statuses  - 訂單狀態
├── statuses        - 通用狀態
└── roles           - 用戶角色

多媒體 (2)
├── images          - 產品圖片
└── product_units   - 產品-單位關聯

其他 (1)
└── site_contents   - 網站內容
```

---

## 💾 資料增長預測

| 表格 | 1年 | 3年 | 分區建議 |
|------|-----|-----|--------|
| orders | 100 MB | 1 GB | ✅ 按季度 |
| order_items | 500 MB | 5 GB | ✅ 按季度 |
| inventory_ledger | 1 GB | 10 GB | ✅ 按月份 |
| products | < 50 MB | < 100 MB | ❌ |
| users | < 50 MB | < 100 MB | ❌ |

---

## 🔑 常用代碼定義

### 訂單狀態 (order_status_code)
```
1: Pending (待確認)     → 庫存預留
2: Confirmed (已確認)   → 庫存預留
3: Shipped (已出貨)     → 庫存扣除
4: Delivered (已交付)   → 訂單完成
5: Cancelled (已取消)   → 庫存取消預留
6: Returned (已退貨)    → 庫存恢復
```

### 用戶角色 (role_code)
```
1: Admin (管理員)       → 完全訪問
2: Customer (客戶)      → 受限訪問
```

### 配送方式 (delivery_method)
```
1: Home Delivery (宅配)
2: Store Pickup (超商取貨)
3: Farm Pickup (農場自取)
4: Express (快遞)
5: Special (特殊配送)
```

**更多代碼定義請查看**: QUICK_REFERENCE.md → 「代碼速查表」

---

## 🚀 常見任務指南

### 1️⃣ 建立新訂單
```
查詢流程:
1. users 表 → 驗證用戶
2. coupons 表 → 驗證優惠券 (可選)
3. products/product_units → 驗證產品和價格
4. 建立 orders 記錄
5. 建立 order_items 記錄 (多筆)
6. inventory_balances → 預留庫存
7. inventory_ledger → 記錄預留動作
8. cart_items → 清空購物車 (可選)
```
**相關文件**: DATABASE_SCHEMA.md → 「訂單流程」

### 2️⃣ 查詢產品庫存
```
查詢流程:
1. product_units → 查詢可用單位
2. inventory_balances → 查詢庫存結餘
3. 計算: 可用 = actual_stock - reserved_stock
```
**相關文件**: DATA_DICTIONARY.md → 「常見查詢」

### 3️⃣ 追蹤訂單狀態
```
查詢流程:
1. orders → 查詢訂單
2. order_items → 查詢訂單項目
3. inventory_ledger → 查詢庫存變動
4. order_statuses → 查詢郵件範本
```
**相關文件**: ER_DIAGRAMS.md → 「訂單狀態流程圖」

---

## 📐 設計模式

### 多對多關係
```
Products ←→ Units
透過 product_units 表示
- 每個產品可有多個單位
- 每個單位用於多個產品
- 儲存該組合的價格和庫存
```

### 庫存雙層系統
```
inventory_balances      - 當前快照 (易於查詢)
inventory_ledger        - 完整歷史 (用於審計)
```

### 狀態分層
```
orders.status_code          - 基本狀態
orders.order_status_code    - 詳細狀態
```

---

## ⚠️ 重要概念

### 金額儲存
- **單位**: 分 (¥0.01)
- **例**: 100 分 = ¥1.00
- **原因**: 避免浮點數精度問題

### 時區處理
- **儲存**: UTC+0 (Zulu Time)
- **應用**: 需要轉換為本地時間

### 級聯刪除
- ⚠️ 刪除 users → 自動刪除 orders, carts
- ⚠️ 刪除 products → 自動刪除 images, product_units

### 軟刪除
- ❌ 目前未使用
- ⚠️ 刪除是永久的

---

## 🔐 安全性檢查清單

### ❌ 不要做
- ❌ 儲存明文密碼
- ❌ 在日誌中列印敏感資訊
- ❌ 暴露 bank_transfer_last5 給非管理員
- ❌ 允許直接修改 inventory_ledger

### ✅ 要做
- ✅ 使用 password_hash
- ✅ 記錄操作人員 (operator_user_id)
- ✅ 驗證用戶權限 (role_code)
- ✅ 在事務中執行多表操作
- ✅ 定期備份

---

## 📚 推薦閱讀順序

### 👶 新手
1. **QUICK_REFERENCE.md** (5 分鐘)
   - 快速了解表格結構和代碼

2. **ER_DIAGRAMS.md** (15 分鐘)
   - 理解表格之間的關係

3. **DATABASE_SCHEMA.md** (30 分鐘)
   - 深入理解設計和約束

### 👨‍💻 開發者
1. **QUICK_REFERENCE.md** (5 分鐘)
   - 快速查詢和參考

2. **DATA_DICTIONARY.md** (按需)
   - 查詢細節和代碼定義

3. **DATABASE_SCHEMA.md** (按需)
   - 理解複雜邏輯

### 🏛️ DBA/架構師
1. **DATABASE_SCHEMA.md** (全部)
   - 完整的架構設計

2. **DATA_DICTIONARY.md** (全部)
   - 完整的規範說明

3. **ER_DIAGRAMS.md** (全部)
   - 視覺化理解

---

## 🛠️ 使用工具

### 查看 Mermaid 圖表
- ✅ GitHub (自動渲染)
- ✅ VS Code (Markdown Preview 或擴展)
- ✅ Obsidian
- ✅ Notion

### 快速搜尋
使用 Ctrl+F 搜尋:
- 表格名稱: `products`, `orders`
- 欄位名稱: `customer_email`, `total_amount`
- 代碼: `order_status_code`

### 複製表格
所有表格可直接複製到 Excel

---

## 📞 支援

### 報告問題
1. 開立 Issue
2. 提供文件名和章節位置
3. 描述問題

### 功能請求
1. 評估業務需求
2. 檢查現有表格是否可用
3. 提交 Pull Request 或 Issue

---

## 📋 文件統計

| 指標 | 數值 |
|------|------|
| 文件數量 | 4 份 |
| 總行數 | ~1,400+ 行 |
| 總字數 | ~5,000+ 字 |
| 表格數量 | 17 個 |
| 代碼定義 | 30+ 個 |
| Mermaid 圖表 | 10+ 個 |

---

## 📅 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0 | 2026-06-24 | 初始版本 |

---

## ✨ 特別感謝

感謝所有貢獻者和使用者的支援與回饋！

---

**最後更新**: 2026-06-24  
**下一次審查**: 2026-09-24
