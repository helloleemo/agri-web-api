from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
import app.modules.orders.model  # noqa: F401
import app.modules.products.model  # noqa: F401
import app.modules.roles.model  # noqa: F401
import app.modules.statuses.model  # noqa: F401
import app.modules.users.model  # noqa: F401
from app.modules.products.router import router as products_router
from app.modules.users.router import router as users_router
from app.modules.orders.router import router as orders_router
from app.modules.common.exception_handlers import register_exception_handlers


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

register_exception_handlers(app)
app.include_router(products_router)
app.include_router(users_router)
app.include_router(orders_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}