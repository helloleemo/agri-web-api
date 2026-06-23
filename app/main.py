from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.base import Base
from app.db.session import engine
import app.modules.orders.model  # noqa: F401
import app.modules.order_statuses.model  # noqa: F401
import app.modules.coupons.model  # noqa: F401
import app.modules.images.model  # noqa: F401
import app.modules.products.model  # noqa: F401
import app.modules.units.model  # noqa: F401
import app.modules.inventories.model  # noqa: F401
import app.modules.roles.model  # noqa: F401
import app.modules.statuses.model  # noqa: F401
import app.modules.users.model  # noqa: F401
import app.modules.carts.model  # noqa: F401
import app.modules.site_contents.model  # noqa: F401
from app.modules.products.router import router as products_router
from app.modules.auth.router import router as auth_router 
from app.modules.users.router import router as users_router
from app.modules.orders.router import router as orders_router
from app.modules.order_statuses.router import router as order_statuses_router
from app.modules.coupons.router import router as coupons_router
from app.modules.images.router import router as images_router
from app.modules.categories.router import router as categories_router
from app.modules.units.router import router as units_router
from app.modules.inventories.router import router as inventories_router
from app.modules.carts.router import router as cart_router
from app.modules.site_contents.router import router as site_contents_router
from app.modules.common.exception_handlers import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

Path("uploads").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Agri API",
    description="農產品管理 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://agri-web-krbu.onrender.com",
        "https://agri-admin.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
)

register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(users_router)
app.include_router(orders_router)
app.include_router(order_statuses_router)
app.include_router(coupons_router)
app.include_router(images_router)
app.include_router(categories_router)
app.include_router(units_router)
app.include_router(inventories_router)
app.include_router(cart_router)
app.include_router(site_contents_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}