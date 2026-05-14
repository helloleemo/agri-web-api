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
from app.modules.products.model import Product
from app.modules.orders.model import Order, OrderItem  


def seed_statuses(db):
    if db.query(Status).count() > 0:
        print("  [跳過] statuses 已有資料")
        return

    statuses = [
        # 所有狀態
        Status(code=1, name="enabled",    category="general"),
        Status(code=2, name="disabled",      category="general"),
        Status(code=3, name="deleted",      category="general"),
    ]
    db.add_all(statuses)
    db.flush()
    print(f"  [完成] 新增 {len(statuses)} 筆 statuses")


def seed_roles(db):
    if db.query(Role).count() > 0:
        print("  [跳過] roles 已有資料")
        return

    roles = [
        Role(id=uuid.uuid4(), name="admin",    code=1),
        Role(id=uuid.uuid4(), name="staff",    code=2),
        Role(id=uuid.uuid4(), name="customer", code=3),
    ]
    db.add_all(roles)
    db.flush()
    print(f"  [完成] 新增 {len(roles)} 筆 roles")


def seed_users(db):
    if db.query(User).count() > 0:
        print("  [跳過] users 已有資料")
        return

    admin_role = db.query(Role).filter_by(code=1).first()
    active_status = db.query(Status).filter_by(code=1).first()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    users = [
        User(
            id=uuid.uuid4(),
            email="admin@agri.com",
            user_name="admin",
            password_hash="hashed_password_placeholder",
            role_id=admin_role.id,
            status_id=active_status.id,
            created_at=now,
            updated_at=now,
        ),
    ]
    db.add_all(users)
    db.flush()
    print(f"  [完成] 新增 {len(users)} 筆 users")


def seed_products(db):
    if db.query(Product).count() > 0:
        print("  [跳過] products 已有資料")
        return

    active_status = db.query(Status).filter_by(code=1).first()

    products = [
        Product(
            id=uuid.uuid4(),
            name="有機蘋果",
            category="fruit",
            origin="台灣",
            unit="kg",
            price=120,
            stock=500,
            description="來自台灣高山的有機蘋果",
            status_id=active_status.id,
        ),
        Product(
            id=uuid.uuid4(),
            name="有機番茄",
            category="vegetable",
            origin="台灣",
            unit="kg",
            price=80,
            stock=300,
            description="新鮮有機番茄，無農藥",
            status_id=active_status.id,
        ),
        Product(
            id=uuid.uuid4(),
            name="有機地瓜",
            category="vegetable",
            origin="台灣",
            unit="kg",
            price=60,
            stock=400,
            description="台南有機地瓜",
            status_id=active_status.id,
        ),
    ]
    db.add_all(products)
    db.flush()
    print(f"  [完成] 新增 {len(products)} 筆 products")


def seed():
    db = SessionLocal()
    try:
        print("開始 seed...")
        seed_statuses(db)
        seed_roles(db)
        seed_users(db)
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
