import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import uuid
from datetime import datetime, timezone

from app.db.session import SessionLocal

from app.modules.statuses.model import Status
from app.modules.roles.model import Role
from app.modules.users.model import User
from app.modules.categories.model import Category
from app.modules.images.model import Image  # noqa: F401
from app.modules.products.model import Product, ProductUnits
from app.modules.units.model import Unit
from app.modules.orders.model import Order, OrderItem  
from app.modules.roles.constants import RoleCode
from app.modules.statuses.constants import StatusCode


def seed_statuses(db):
    status_definitions = [
        {"code": 1, "name": "enabled"},
        {"code": 2, "name": "disabled"},
        {"code": 3, "name": "deleted"},
    ]

    created_count = 0
    for item in status_definitions:
        status = db.query(Status).filter_by(code=item["code"]).first()
        if status:
            status.name = item["name"]
            continue

        db.add(Status(**item))
        created_count += 1

    db.flush()
    if created_count == 0:
        print("  [跳過] statuses 已對齊")
    else:
        print(f"  [完成] 新增 {created_count} 筆 statuses")


def seed_roles(db):
    role_definitions = [
        {"name": "admin", "code": RoleCode.ROLE_ADMIN.value},
        {"name": "staff", "code": RoleCode.ROLE_STAFF.value},
        {"name": "member", "code": RoleCode.ROLE_MEMBER.value},
    ]

    created_count = 0
    for item in role_definitions:
        role = db.query(Role).filter_by(code=item["code"]).first()
        if role:
            if role.name != item["name"]:
                role.name = item["name"]
            continue

        db.add(Role(id=uuid.uuid4(), name=item["name"], code=item["code"]))
        created_count += 1

    db.flush()
    if created_count == 0:
        print("  [跳過] roles 已對齊")
    else:
        print(f"  [完成] 新增 {created_count} 筆 roles")


def seed_users(db):
    if db.query(User).count() > 0:
        print("  [跳過] users 已有資料")
        return

    now = datetime.now(timezone.utc)

    users = [
        User(
            id=uuid.uuid4(),
            email="admin@agri.com",
            user_name="admin",
            password_hash="hashed_password_placeholder",
            role_code=RoleCode.ROLE_ADMIN.value,
            status_code=StatusCode.ENABLED.value,
            created_at=now,
            updated_at=now,
        ),
    ]
    db.add_all(users)
    db.flush()
    print(f"  [完成] 新增 {len(users)} 筆 users")


def seed_categories(db):
    category_definitions = [
        {"name": "fruit", "meta_data": {"display_name": "水果"}},
        {"name": "vegetable", "meta_data": {"display_name": "蔬菜"}},
        {"name": "grain", "meta_data": {"display_name": "穀物"}},
    ]

    created_count = 0
    for item in category_definitions:
        category = db.query(Category).filter_by(name=item["name"]).first()
        if category:
            category.meta_data = item["meta_data"]
            continue

        db.add(
            Category(
                id=uuid.uuid4(),
                name=item["name"],
                meta_data=item["meta_data"],
            )
        )
        created_count += 1

    db.flush()
    if created_count == 0:
        print("  [跳過] categories 已對齊")
    else:
        print(f"  [完成] 新增 {created_count} 筆 categories")


def seed_units(db):
    unit_definitions = ["kg", "g", "box", "bag", "pcs"]

    created_count = 0
    for name in unit_definitions:
        unit = db.query(Unit).filter_by(name=name).first()
        if unit:
            continue

        db.add(Unit(id=uuid.uuid4(), name=name))
        created_count += 1

    db.flush()
    if created_count == 0:
        print("  [跳過] units 已對齊")
    else:
        print(f"  [完成] 新增 {created_count} 筆 units")


def seed_products(db):
    category_map = {
        category.name: category.id
        for category in db.query(Category).filter(Category.name.in_(["fruit", "vegetable", "grain"]))
    }
    unit_map = {unit.name: unit.id for unit in db.query(Unit).all()}

    required_categories = {"fruit", "vegetable", "grain"}
    if set(category_map.keys()) != required_categories:
        missing = required_categories - set(category_map.keys())
        raise ValueError(f"缺少 category seed: {sorted(missing)}")

    required_units = {"kg", "box", "bag", "pcs"}
    missing_units = required_units - set(unit_map.keys())
    if missing_units:
        raise ValueError(f"缺少 unit seed: {sorted(missing_units)}")

    product_definitions = [
        {
            "name": "有機蘋果",
            "category": "fruit",
            "origin": "台灣",
            "price": 120,
            "stock": 500,
            "units": [
                {"name": "kg", "price": 120, "stock": 500},
                {"name": "box", "price": 680, "stock": 45},
                {"name": "pcs", "price": 28, "stock": 1200},
            ],
            "description": "來自台灣高山的有機蘋果",
        },
        {
            "name": "有機香蕉",
            "category": "fruit",
            "origin": "台灣",
            "price": 95,
            "stock": 420,
            "units": [
                {"name": "kg", "price": 95, "stock": 420},
                {"name": "box", "price": 520, "stock": 38},
                {"name": "bag", "price": 155, "stock": 160},
            ],
            "description": "香甜軟糯的有機香蕉",
        },
        {
            "name": "有機芭樂",
            "category": "fruit",
            "origin": "台灣",
            "price": 110,
            "stock": 260,
            "units": [
                {"name": "kg", "price": 110, "stock": 260},
                {"name": "box", "price": 610, "stock": 25},
                {"name": "pcs", "price": 35, "stock": 820},
            ],
            "description": "清脆多汁的白肉芭樂",
        },
        {
            "name": "有機番茄",
            "category": "vegetable",
            "origin": "台灣",
            "price": 80,
            "stock": 300,
            "units": [
                {"name": "kg", "price": 80, "stock": 300},
                {"name": "box", "price": 430, "stock": 30},
                {"name": "bag", "price": 135, "stock": 180},
            ],
            "description": "新鮮有機番茄，無農藥",
        },
        {
            "name": "有機地瓜",
            "category": "vegetable",
            "origin": "台灣",
            "price": 60,
            "stock": 400,
            "units": [
                {"name": "kg", "price": 60, "stock": 400},
                {"name": "box", "price": 330, "stock": 42},
                {"name": "bag", "price": 115, "stock": 210},
            ],
            "description": "台南有機地瓜",
        },
        {
            "name": "有機高麗菜",
            "category": "vegetable",
            "origin": "台灣",
            "price": 70,
            "stock": 350,
            "units": [
                {"name": "kg", "price": 70, "stock": 350},
                {"name": "box", "price": 390, "stock": 33},
                {"name": "pcs", "price": 65, "stock": 480},
            ],
            "description": "高山栽種，口感爽脆",
        },
        {
            "name": "有機紅蘿蔔",
            "category": "vegetable",
            "origin": "台灣",
            "price": 65,
            "stock": 280,
            "units": [
                {"name": "kg", "price": 65, "stock": 280},
                {"name": "box", "price": 350, "stock": 29},
                {"name": "bag", "price": 120, "stock": 175},
            ],
            "description": "自然甜味，適合燉煮與沙拉",
        },
        {
            "name": "有機白米",
            "category": "grain",
            "origin": "台灣",
            "price": 90,
            "stock": 600,
            "units": [
                {"name": "kg", "price": 90, "stock": 600},
                {"name": "bag", "price": 430, "stock": 120},
                {"name": "box", "price": 1680, "stock": 26},
            ],
            "description": "友善耕作白米，米香濃郁",
        },
        {
            "name": "有機糙米",
            "category": "grain",
            "origin": "台灣",
            "price": 105,
            "stock": 450,
            "units": [
                {"name": "kg", "price": 105, "stock": 450},
                {"name": "bag", "price": 500, "stock": 95},
                {"name": "box", "price": 1950, "stock": 21},
            ],
            "description": "保留麩皮與胚芽，營養豐富",
        },
        {
            "name": "有機燕麥",
            "category": "grain",
            "origin": "加拿大",
            "price": 130,
            "stock": 320,
            "units": [
                {"name": "kg", "price": 130, "stock": 320},
                {"name": "bag", "price": 620, "stock": 72},
                {"name": "box", "price": 2400, "stock": 16},
            ],
            "description": "高纖有機燕麥，適合早餐料理",
        },
    ]

    created_count = 0
    for item in product_definitions:
        product = db.query(Product).filter_by(name=item["name"]).first()
        payload = {
            "name": item["name"],
            "category_id": category_map[item["category"]],
            "origin": item["origin"],
            "price": item["price"],
            "stock": item["stock"],
            "description": item["description"],
            "status_code": StatusCode.ENABLED.value,
        }

        if product:
            for key, value in payload.items():
                setattr(product, key, value)
        else:
            product = Product(id=uuid.uuid4(), **payload)
            db.add(product)
            created_count += 1

        db.flush()

        for unit_item in item["units"]:
            unit_id = unit_map[unit_item["name"]]
            product_unit = (
                db.query(ProductUnits)
                .filter_by(product_id=product.id, unit_id=unit_id)
                .first()
            )
            if product_unit:
                product_unit.price = unit_item["price"]
                product_unit.stock = unit_item["stock"]
            else:
                db.add(
                    ProductUnits(
                        product_id=product.id,
                        unit_id=unit_id,
                        price=unit_item["price"],
                        stock=unit_item["stock"],
                    )
                )

    db.flush()
    if created_count == 0:
        print("  [跳過] products 已對齊")
    else:
        print(f"  [完成] 新增 {created_count} 筆 products")


def seed():
    db = SessionLocal()
    try:
        print("開始 seed...")
        seed_statuses(db)
        seed_roles(db)
        seed_users(db)
        seed_categories(db)
        seed_units(db)
        seed_products(db)
        db.commit()
        print("Seed 完成！")
    except Exception as e:
        db.rollback()
        print(f"Seed 失敗：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
