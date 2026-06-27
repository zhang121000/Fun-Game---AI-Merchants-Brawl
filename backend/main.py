import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import init_db
from api import merchants, products, customers, cart, orders, marketing, admin, analytics
import ai.providers  # noqa: F401 — 注册所有 AI Provider


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from services.seed_service import seed_data_if_empty
    await seed_data_if_empty()
    yield


app = FastAPI(title="AI 保健品电商平台", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchants.router, prefix="/api/v1", tags=["商家"])
app.include_router(products.router, prefix="/api/v1", tags=["商品"])
app.include_router(customers.router, prefix="/api/v1", tags=["顾客"])
app.include_router(cart.router, prefix="/api/v1", tags=["购物车"])
app.include_router(orders.router, prefix="/api/v1", tags=["订单"])
app.include_router(marketing.router, prefix="/api/v1", tags=["营销策略"])
app.include_router(admin.router, prefix="/api/v1", tags=["管理员"])
app.include_router(analytics.router, prefix="/api/v1", tags=["数据分析"])


@app.get("/")
async def root():
    return {"message": "AI 保健品电商平台 API", "docs": "/docs"}
