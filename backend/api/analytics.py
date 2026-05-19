from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.order import Order, OrderItem
from models.product import Product
from models.merchant import Merchant
from models.customer import Customer

router = APIRouter()


@router.get("/analytics/sales-trend")
async def sales_trend(
    dimension: str = "ai",
    db: AsyncSession = Depends(get_db),
):
    """销售趋势 — 支持按人群/品类/AI商家三种维度

    dimension: "demographic" | "category" | "ai"
    """
    from models.marketing import DailyDecision

    if dimension == "demographic":
        # 按人群：从 DailyDecision.target_focus 聚合（当日 AI 定向了哪个人群）
        # 但更准确的方式是：遍历订单按购买者人群分
        result = await db.execute(
            select(
                Order.simulated_day.label("day"),
                Customer.demographic.label("key"),
                func.count(OrderItem.id).label("orders"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Customer, Order.customer_id == Customer.id)
            .where(Order.is_simulated == True, Order.simulated_day > 0)
            .group_by(Order.simulated_day, Customer.demographic)
            .order_by(Order.simulated_day)
        )
    elif dimension == "category":
        # 按品类
        result = await db.execute(
            select(
                Order.simulated_day.label("day"),
                Product.category.label("key"),
                func.count(OrderItem.id).label("orders"),
            )
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .where(Order.is_simulated == True, Order.simulated_day > 0)
            .group_by(Order.simulated_day, Product.category)
            .order_by(Order.simulated_day)
        )
    else:
        # 按 AI 商家
        from models.marketing import DailyDecision as DD
        result = await db.execute(
            select(
                DD.day.label("day"),
                DD.merchant_ai.label("key"),
                func.sum(DD.units_sold).label("orders"),
            )
            .group_by(DD.day, DD.merchant_ai)
            .order_by(DD.day)
        )

    rows = result.all()

    # 转换为 { day -> { key -> value } } 格式，方便前端画折线图
    series: dict[str, dict[int, int]] = {}
    for r in rows:
        key = r.key
        day = int(r.day)
        if key not in series:
            series[key] = {}
        series[key][day] = int(r.orders or 0)

    # 确保所有天数连续
    all_days = sorted(set(d for s in series.values() for d in s.keys()))
    if not all_days:
        all_days = [0]

    return {
        "days": all_days,
        "series": {
            key: [vals.get(d, 0) for d in all_days]
            for key, vals in series.items()
        },
    }


@router.get("/analytics/demographic-dist")
async def demographic_distribution(db: AsyncSession = Depends(get_db)):
    """按购买者人群统计（不是产品目标人群）"""
    result = await db.execute(
        select(
            Customer.demographic,
            func.count(OrderItem.id).label("count"),
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .group_by(Customer.demographic)
    )
    rows = result.all()
    return [{"demographic": r.demographic, "count": r.count, "revenue": float(r.revenue)} for r in rows]


@router.get("/analytics/product-compare")
async def product_comparison(db: AsyncSession = Depends(get_db)):
    """各产品销售对比（含 AI 模型标识）"""
    result = await db.execute(
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Product.ai_model,
            Product.category,
            func.count(OrderItem.id).label("orders"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
    )
    rows = result.all()
    return [{
        "product_id": r.product_id, "product_name": r.product_name,
        "ai_model": r.ai_model, "category": r.category,
        "orders": r.orders, "units_sold": int(r.units_sold), "revenue": float(r.revenue),
    } for r in rows]


@router.get("/analytics/product/{product_id}/demographic-breakdown")
async def product_demographic_breakdown(product_id: int, db: AsyncSession = Depends(get_db)):
    """单个产品的购买者人群分布"""
    result = await db.execute(
        select(
            Customer.demographic,
            func.count(OrderItem.id).label("count"),
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .where(OrderItem.product_id == product_id)
        .group_by(Customer.demographic)
    )
    rows = result.all()
    return [{"demographic": r.demographic, "count": r.count, "revenue": float(r.revenue)} for r in rows]


@router.get("/analytics/top-products")
async def top_products(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Product.name.label("product_name"),
            Product.ai_model,
            func.sum(OrderItem.quantity).label("total_sold"),
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
    )
    rows = result.all()
    return [{
        "product_name": r.product_name, "ai_model": r.ai_model,
        "total_sold": int(r.total_sold), "revenue": float(r.revenue),
    } for r in rows]
