# 資料表關係圖 (Database ER Diagram)

## 簡化的實體關係圖

```mermaid
graph TB
    subgraph Users["用戶與認證"]
        Users["<b>users</b><br/>id, email, user_name<br/>role_code → roles<br/>status_code → statuses"]
        Roles["<b>roles</b><br/>id, code, name"]
    end

    subgraph Products["產品與分類"]
        Products["<b>products</b><br/>id, name, price, stock<br/>category_id → categories<br/>status_code → statuses"]
        Categories["<b>categories</b><br/>id, name, meta_data"]
        Units["<b>units</b><br/>id, name"]
        ProductUnits["<b>product_units</b><br/>product_id, unit_id<br/>price, stock<br/>(多對多關聯)"]
        Images["<b>images</b><br/>id, product_id, file_url<br/>is_primary, sort_order"]
    end

    subgraph Orders["訂單系統"]
        Orders["<b>orders</b><br/>id, order_no, customer_email<br/>user_id → users<br/>order_status_code → order_statuses<br/>status_code → statuses"]
        OrderItems["<b>order_items</b><br/>id, order_id, product_id<br/>unit_id, quantity"]
        OrderStatuses["<b>order_statuses</b><br/>id, code, name<br/>郵件範本"]
    end

    subgraph Shopping["購物車"]
        Carts["<b>carts</b><br/>id, user_id (唯一)"]
        CartItems["<b>cart_items</b><br/>id, cart_id, product_id<br/>unit_id, quantity"]
    end

    subgraph Inventory["庫存管理"]
        InventoryBalance["<b>inventory_balances</b><br/>id, product_id, unit_id<br/>initial_stock, actual_stock<br/>reserved_stock"]
        InventoryLedger["<b>inventory_ledger</b><br/>id, product_id, unit_id<br/>order_item_id, action<br/>delta_actual, delta_reserved<br/>operator_user_id → users"]
    end

    subgraph Promotions["促銷"]
        Coupons["<b>coupons</b><br/>id, code, name<br/>discount_type, discount_value<br/>status_code → statuses"]
    end

    subgraph System["系統配置"]
        Statuses["<b>statuses</b><br/>id, code, name<br/>(產品狀態, 用戶狀態等)"]
        SiteContents["<b>site_contents</b><br/>id, page_key<br/>content_data (JSONB)"]
    end

    %% 用戶關係
    Users --> Roles
    Users --> Statuses

    %% 產品關係
    Products --> Categories
    Products --> Statuses
    Products --> ProductUnits
    ProductUnits --> Units
    Products --> Images

    %% 訂單關係
    Orders --> Users
    Orders --> OrderStatuses
    Orders --> Statuses
    Orders --> OrderItems
    OrderItems --> Products
    OrderItems --> Units

    %% 購物車關係
    Carts --> Users
    CartItems --> Carts
    CartItems --> Products
    CartItems --> Units

    %% 庫存關係
    Products --> InventoryBalance
    Units --> InventoryBalance
    Products --> InventoryLedger
    Units --> InventoryLedger
    OrderItems --> InventoryLedger
    Orders --> InventoryLedger
    Users --> InventoryLedger

    %% 促銷
    Coupons --> Statuses

    style Users fill:#e1f5ff
    style Products fill:#f3e5f5
    style Orders fill:#fff3e0
    style Shopping fill:#e8f5e9
    style Inventory fill:#fce4ec
    style Promotions fill:#f1f8e9
    style System fill:#ede7f6
```

---

## 表格分層關係圖

```mermaid
graph LR
    A["<b>核心表格</b><br/>users<br/>products<br/>categories<br/>units<br/>statuses<br/>roles"]
    
    B["<b>關聯表格</b><br/>product_units<br/>carts"]
    
    C["<b>業務表格</b><br/>orders<br/>order_items<br/>cart_items"]
    
    D["<b>支援表格</b><br/>images<br/>coupons<br/>order_statuses"]
    
    E["<b>審計表格</b><br/>inventory_balances<br/>inventory_ledger"]
    
    F["<b>配置表格</b><br/>site_contents"]
    
    A --> B
    B --> C
    A --> C
    A --> D
    C --> E
    A --> E
    A --> F
    
    style A fill:#bbdefb
    style B fill:#c8e6c9
    style C fill:#ffe0b2
    style D fill:#f8bbd0
    style E fill:#f0f4c3
    style F fill:#e1bee7
```

---

## 資料流向圖

```mermaid
sequenceDiagram
    participant 客戶 as 客戶<br/>(Customer)
    participant 用戶系統 as 用戶系統<br/>(Users)
    participant 購物車 as 購物車<br/>(Carts/CartItems)
    participant 產品 as 產品系統<br/>(Products/Units)
    participant 訂單 as 訂單系統<br/>(Orders/OrderItems)
    participant 庫存 as 庫存系統<br/>(Inventory)

    Note over 客戶,庫存: 典型購物流程

    客戶->>用戶系統: 1. 註冊/登入
    activate 用戶系統
    用戶系統-->>客戶: 取得 user_id
    deactivate 用戶系統

    客戶->>購物車: 2. 瀏覽產品
    activate 產品
    產品-->>購物車: 返回產品資訊
    deactivate 產品

    客戶->>購物車: 3. 加入購物車
    activate 購物車
    購物車->>產品: 查詢單位/價格
    產品-->>購物車: 返回 ProductUnits
    購物車-->>客戶: 確認加入
    deactivate 購物車

    客戶->>訂單: 4. 結帳
    activate 訂單
    訂單->>購物車: 取得購物車項目
    購物車-->>訂單: 返回 CartItems
    訂單->>庫存: 預留庫存
    activate 庫存
    庫存->>庫存: 更新 InventoryBalance
    庫存->>庫存: 記錄到 InventoryLedger
    庫存-->>訂單: 庫存預留成功
    deactivate 庫存
    訂單->>訂單: 建立 Order + OrderItems
    訂單-->>客戶: 訂單確認 (order_no)
    deactivate 訂單

    Note over 庫存: 訂單進度變更時更新庫存
```

---

## 庫存管理流程圖

```mermaid
graph TD
    A["訂單建立<br/>(Order Created)"] --> B["預留庫存<br/>(Reserve Stock)<br/>reserved_stock += qty"]
    
    B --> C{"訂單狀態<br/>變更"}
    
    C -->|已出貨| D["提交實際出貨<br/>(Fulfill)<br/>actual_stock -= qty<br/>reserved_stock -= qty"]
    
    C -->|已取消| E["取消預留<br/>(Release)<br/>reserved_stock -= qty"]
    
    C -->|退貨| F["增加庫存<br/>(Return)<br/>actual_stock += qty"]
    
    D --> G["記錄到 InventoryLedger"]
    E --> G
    F --> G
    
    G --> H["更新 InventoryBalance"]
    
    style A fill:#fff9c4
    style B fill:#ffcc80
    style D fill:#a5d6a7
    style E fill:#ef9a9a
    style F fill:#90caf9
    style G fill:#ce93d8
    style H fill:#b0bec5
```

---

## 訂單狀態流程圖

```mermaid
stateDiagram-v2
    [*] --> 待確認: Order Created
    
    待確認 --> 待出貨: Order Confirmed
    待確認 --> 已取消: Order Cancelled
    
    待出貨 --> 已出貨: Shipped
    待出貨 --> 已取消: Order Cancelled
    
    已出貨 --> 已交付: Delivered
    已出貨 --> 待退貨: Return Requested
    
    已交付 --> [*]
    待退貨 --> 已退貨: Return Completed
    已取消 --> [*]
    已退貨 --> [*]
    
    note right of 待確認
        order_status_code = 1
        庫存: 預留
    end note
    
    note right of 待出貨
        order_status_code = 2
        庫存: 預留中
    end note
    
    note right of 已出貨
        order_status_code = 3
        庫存: 已扣除
    end note
    
    note right of 已交付
        order_status_code = 4
        訂單完成
    end note
```

---

## 使用者與權限關係圖

```mermaid
graph TB
    User["<b>users</b>"]
    Role["<b>roles</b>"]
    Status["<b>statuses</b>"]
    
    Admin["角色代碼 = 1<br/>管理員<br/>- 建立/編輯產品<br/>- 建立優惠券<br/>- 檢視所有訂單<br/>- 庫存調整"]
    
    Customer["角色代碼 = 2<br/>客戶<br/>- 下訂單<br/>- 檢視自己的訂單<br/>- 管理購物車"]
    
    Active["狀態代碼 = 1<br/>活躍<br/>可以登入"]
    
    Inactive["狀態代碼 = 0<br/>停用<br/>無法登入"]
    
    User -->|role_code| Role
    Role --> Admin
    Role --> Customer
    
    User -->|status_code| Status
    Status --> Active
    Status --> Inactive
    
    style User fill:#bbdefb
    style Role fill:#c8e6c9
    style Status fill:#ffccbc
    style Admin fill:#a5d6a7
    style Customer fill:#a5d6a7
    style Active fill:#81c784
    style Inactive fill:#e57373
```

---

## 產品與庫存關係圖

```mermaid
graph TD
    Product["<b>products</b><br/>- name<br/>- price (基礎價格)<br/>- stock (基礎庫存)<br/>- category_id<br/>- status_code"]
    
    Unit["<b>units</b><br/>- name<br/>例: kg, 箱, 個"]
    
    ProductUnits["<b>product_units</b><br/>(多對多關聯)<br/>- product_id<br/>- unit_id<br/>- price (該單位的價格)<br/>- stock (該單位的庫存)"]
    
    InventoryBalance["<b>inventory_balances</b><br/>- product_id<br/>- unit_id<br/>- initial_stock (初始)<br/>- actual_stock (實際)<br/>- reserved_stock (預留)"]
    
    InventoryLedger["<b>inventory_ledger</b><br/>(審計日誌)<br/>- product_id<br/>- unit_id<br/>- action<br/>- delta_actual<br/>- delta_reserved<br/>- operator_user_id"]
    
    Product -->|1對多| ProductUnits
    Unit -->|1對多| ProductUnits
    
    ProductUnits -->|同步到| InventoryBalance
    InventoryBalance -->|記錄變動| InventoryLedger
    
    style Product fill:#bbdefb
    style Unit fill:#c8e6c9
    style ProductUnits fill:#ffe0b2
    style InventoryBalance fill:#f0f4c3
    style InventoryLedger fill:#e1bee7
```

---

## 訂單與項目關係圖

```mermaid
graph TD
    Order["<b>orders</b><br/>- order_no (訂單編號)<br/>- user_id<br/>- customer_email<br/>- total_amount<br/>- order_status_code<br/>- status_code"]
    
    OrderItem["<b>order_items</b><br/>- order_id<br/>- product_id<br/>- unit_id<br/>- unit (單位文字)<br/>- quantity"]
    
    Product["<b>products</b>"]
    Unit["<b>units</b>"]
    
    InventoryLedger["<b>inventory_ledger</b><br/>記錄庫存變動"]
    
    User["<b>users</b>"]
    OrderStatus["<b>order_statuses</b><br/>郵件範本"]
    
    User -->|下單| Order
    Order -->|1對多| OrderItem
    OrderItem -->|引用| Product
    OrderItem -->|引用| Unit
    OrderItem -->|觸發| InventoryLedger
    Order -->|參考| OrderStatus
    
    style Order fill:#fff9c4
    style OrderItem fill:#ffcc80
    style Product fill:#a5d6a7
    style Unit fill:#a5d6a7
    style InventoryLedger fill:#90caf9
    style User fill:#bbdefb
    style OrderStatus fill:#ce93d8
```

---

## 快速參考：外鍵關係表

| 表格 | 外鍵 | 參考表格 | 說明 |
|------|------|---------|------|
| users | role_code | roles | 用戶角色 |
| users | status_code | statuses | 用戶狀態 |
| products | category_id | categories | 產品分類 |
| products | status_code | statuses | 產品狀態 |
| product_units | product_id | products | 產考產品 |
| product_units | unit_id | units | 參考單位 |
| images | product_id | products | 所屬產品 |
| orders | user_id | users | 訂購用戶 |
| orders | order_status_code | order_statuses | 訂單處理狀態 |
| orders | status_code | statuses | 訂單基本狀態 |
| order_items | order_id | orders | 所屬訂單 |
| order_items | product_id | products | 訂購產品 |
| order_items | unit_id | units | 選擇單位 (可選) |
| carts | user_id | users | 用戶購物車 |
| cart_items | cart_id | carts | 所屬購物車 |
| cart_items | product_id | products | 購物車中的產品 |
| cart_items | unit_id | units | 選擇單位 (可選) |
| coupons | status_code | statuses | 優惠券狀態 |
| inventory_balances | product_id | products | 產品庫存 |
| inventory_balances | unit_id | units | 單位庫存 |
| inventory_ledger | product_id | products | 產品 |
| inventory_ledger | unit_id | units | 單位 |
| inventory_ledger | order_id | orders | 關聯訂單 (可選) |
| inventory_ledger | order_item_id | order_items | 關聯訂單項目 (可選) |
| inventory_ledger | operator_user_id | users | 操作人員 (可選) |

---

## 文件更新

- **建立日期**: 2026-06-24
- **最後更新**: 2026-06-24
