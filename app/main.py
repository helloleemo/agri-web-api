from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.base import Base
from app.db.session import engine
from app.modules.products.router import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時：建立所有資料表（開發期用，正式環境換 Alembic）
    Base.metadata.create_all(bind=engine)
    yield
    # 關閉時：可以在這裡加清理邏輯


app = FastAPI(
    title="Agri API",
    description="農產品管理 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(products_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}