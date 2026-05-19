import asyncio
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db, async_session
from models.order import Order
from models.merchant import Merchant
from models.customer import Customer
from models.product import Product
from models.marketing import (
    MarketingStrategy, SimulationState, DailyDecision,
    PlatformAllocation, ResearchProject,
)

router = APIRouter()

# 模拟状态追踪
_simulation_lock = asyncio.Lock()
_simulation_status = {"running": False, "day": 0, "result": None, "error": None, "ai_completed": []}


@router.get("/admin/overview")
async def admin_overview(db: AsyncSession = Depends(get_db)):
    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar() or 0
    total_revenue = (await db.execute(select(func.coalesce(func.sum(Order.total_amount), 0)))).scalar() or 0
    total_merchants = (await db.execute(select(func.count()).select_from(Merchant))).scalar() or 0
    total_customers = (await db.execute(select(func.count()).select_from(Customer))).scalar() or 0
    total_products = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0

    # 获取模拟状态
    state = (await db.execute(select(SimulationState))).scalars().first()
    current_day = state.current_day if state else 0

    # 获取待审批策略数
    pending_strategies = (await db.execute(
        select(func.count()).select_from(MarketingStrategy)
        .where(MarketingStrategy.status == "pending")
    )).scalar() or 0

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "total_merchants": total_merchants,
        "total_customers": total_customers,
        "total_products": total_products,
        "current_day": current_day,
        "pending_strategies": pending_strategies,
    }


@router.post("/admin/advance-day")
async def advance_day(
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """推进一天：后台执行，立即返回状态"""
    global _simulation_status

    if _simulation_status["running"]:
        return {
            "status": "running",
            "message": f"模拟已在运行中（第{_simulation_status['day']}天）",
            "day": _simulation_status["day"],
        }

    # 获取当前天数
    state = (await db.execute(select(SimulationState))).scalars().first()
    next_day = (state.current_day if state else 0) + 1

    _simulation_status = {
        "running": True,
        "day": next_day,
        "result": None,
        "error": None,
        "ai_completed": [],
    }

    async def _run_simulation():
        global _simulation_status
        try:
            async with async_session() as new_db:
                from services.day_simulation_service import advance_day as do_advance

                def mark_ai_done(ai_model: str):
                    if ai_model not in _simulation_status["ai_completed"]:
                        _simulation_status["ai_completed"].append(ai_model)

                result = await do_advance(new_db, on_ai_complete=mark_ai_done)
                _simulation_status = {
                    "running": False,
                    "day": result["day"],
                    "result": result,
                    "error": None,
                    "ai_completed": _simulation_status["ai_completed"],
                }
        except Exception as e:
            _simulation_status = {
                "running": False,
                "day": next_day,
                "result": None,
                "error": str(e),
                "ai_completed": _simulation_status.get("ai_completed", []),
            }

    background_tasks.add_task(_run_simulation)

    return {
        "status": "started",
        "day": next_day,
        "message": f"第{next_day}天模拟已启动，调用6个AI决策中...",
    }


@router.get("/admin/advance-day-status")
async def advance_day_status():
    """检查推进状态"""
    return _simulation_status


from pydantic import BaseModel

class RestockBody(BaseModel):
    amount: int


@router.post("/admin/products/{product_id}/restock")
async def admin_restock(product_id: int, body: RestockBody, db: AsyncSession = Depends(get_db)):
    """管理员手动进货"""
    amount = body.amount
    if amount < 1 or amount > 99999:
        return {"error": "进货量需在 1~99999 之间"}

    product = await db.get(Product, product_id)
    if not product:
        return {"error": "产品不存在"}

    product.stock = min(product.stock + amount, 99999)
    await db.commit()
    return {"product_id": product_id, "stock": product.stock, "added": amount}


@router.post("/admin/reset")
async def admin_reset(db: AsyncSession = Depends(get_db)):
    """一键重置：清空所有模拟数据，天数归零，库存恢复"""
    from sqlalchemy import delete
    from models.order import OrderItem

    # 清空所有模拟数据
    await db.execute(delete(OrderItem))
    await db.execute(delete(Order))
    await db.execute(delete(DailyDecision))
    await db.execute(delete(PlatformAllocation))
    await db.execute(delete(ResearchProject))
    await db.execute(delete(SimulationState))

    # 恢复产品库存
    products = (await db.execute(select(Product))).scalars().all()
    for p in products:
        p.stock = 200

    # 重新初始化模拟状态
    db.add(SimulationState(current_day=0))

    global _simulation_status
    _simulation_status = {"running": False, "day": 0, "result": None, "error": None}

    await db.commit()
    return {"status": "ok", "message": "所有数据已清除，天数归零"}

@router.get("/admin/simulation-state")
async def simulation_state(db: AsyncSession = Depends(get_db)):
    state = (await db.execute(select(SimulationState))).scalars().first()
    if not state:
        return {"current_day": 0, "is_running": False}
    return {
        "current_day": state.current_day,
        "is_running": state.is_running,
        "started_at": state.started_at.isoformat() if state.started_at else None,
    }


@router.get("/admin/leaderboard")
async def leaderboard(db: AsyncSession = Depends(get_db)):
    """获取最新排名"""
    state = (await db.execute(select(SimulationState))).scalars().first()
    if not state or state.current_day == 0:
        return {"day": 0, "rankings": []}

    current_day = state.current_day

    # 获取今天所有商家的决策记录
    decisions = (await db.execute(
        select(DailyDecision)
        .where(DailyDecision.day == current_day)
        .order_by(DailyDecision.rank)
    )).scalars().all()

    rankings = []
    for d in decisions:
        # 获取该商家的历史排名（最近7天）
        history = (await db.execute(
            select(DailyDecision.rank, DailyDecision.units_sold)
            .where(DailyDecision.merchant_ai == d.merchant_ai)
            .where(DailyDecision.day >= max(1, current_day - 7))
            .where(DailyDecision.day <= current_day)
            .order_by(DailyDecision.day)
        )).all()

        rankings.append({
            "merchant_ai": d.merchant_ai,
            "category": d.category,
            "product_name": d.product_name,
            "rank": d.rank,
            "units_sold": d.units_sold,
            "revenue": d.revenue,
            "price": d.price,
            "promotion": d.promotion,
            "target_focus": d.target_focus,
            "reasoning": d.reasoning,
            "traffic_received": d.traffic_received,
            "history": [{"rank": h[0], "units": h[1]} for h in history],
        })

    return {"day": current_day, "rankings": rankings}


@router.get("/admin/decision-log")
async def decision_log(day: int = Query(None), db: AsyncSession = Depends(get_db)):
    """获取某天的决策因果链"""
    if day is None:
        state = (await db.execute(select(SimulationState))).scalars().first()
        day = state.current_day if state else 1

    decisions = (await db.execute(
        select(DailyDecision)
        .where(DailyDecision.day == day)
        .order_by(DailyDecision.rank)
    )).scalars().all()

    allocations = (await db.execute(
        select(PlatformAllocation)
        .where(PlatformAllocation.day == day)
    )).scalars().all()

    return {
        "day": day,
        "decisions": [
            {
                "merchant_ai": d.merchant_ai,
                "category": d.category,
                "product_name": d.product_name,
                "price": d.price,
                "promotion": d.promotion,
                "target_focus": d.target_focus,
                "description_update": d.description_update,
                "reasoning": d.reasoning,
                "traffic_received": d.traffic_received,
                "units_sold": d.units_sold,
                "revenue": d.revenue,
                "rank": d.rank,
                "research_product": d.research_product,
            }
            for d in decisions
        ],
        "allocations": [
            {
                "merchant_ai": a.merchant_ai,
                "demographic": a.demographic,
                "traffic_count": a.traffic_count,
            }
            for a in allocations
        ],
    }


@router.get("/admin/platform-suggestions")
async def platform_suggestions(db: AsyncSession = Depends(get_db)):
    """获取平台建议"""
    state = (await db.execute(select(SimulationState))).scalars().first()
    if not state or state.current_day == 0:
        return {"suggestions": []}

    current_day = state.current_day
    decisions = (await db.execute(
        select(DailyDecision)
        .where(DailyDecision.day == current_day)
        .order_by(DailyDecision.rank)
    )).scalars().all()

    if len(decisions) < 2:
        return {"suggestions": []}

    suggestions = []
    last = decisions[-1]

    # 检查连续垫底
    recent = (await db.execute(
        select(DailyDecision)
        .where(DailyDecision.merchant_ai == last.merchant_ai)
        .where(DailyDecision.day >= current_day - 3)
        .where(DailyDecision.day < current_day)
        .order_by(DailyDecision.day.desc())
    )).scalars().all()

    total_merchants = len(decisions)
    consecutive_last = all(d.rank == total_merchants for d in recent)

    if consecutive_last and len(recent) >= 1:
        suggestions.append({
            "merchant_ai": last.merchant_ai,
            "category": last.category,
            "type": "warning",
            "message": f"连续{len(recent)+1}天排名垫底",
            "advice": "建议：1)降价促销冲量 2)研发同品类新品 3)调整目标人群",
        })

    # 检查零销量
    for d in decisions:
        if d.units_sold == 0 and d.traffic_received > 10:
            suggestions.append({
                "merchant_ai": d.merchant_ai,
                "category": d.category,
                "type": "alert",
                "message": f"今日零销量（{d.traffic_received}个流量，转化率0%）",
                "advice": "建议：检查定价是否过高，或产品描述吸引力不足",
            })

    # 检查研发项目
    active_research = (await db.execute(
        select(ResearchProject)
        .where(ResearchProject.status == "active")
    )).scalars().all()

    for r in active_research:
        suggestions.append({
            "merchant_ai": r.merchant_ai,
            "category": r.category,
            "type": "info",
            "message": f"正在研发「{r.product_name}」，还需{r.days_remaining}天上架",
            "advice": "",
        })

    return {"suggestions": suggestions}


@router.get("/admin/research-projects")
async def research_projects(db: AsyncSession = Depends(get_db)):
    """获取所有研发项目"""
    projects = (await db.execute(
        select(ResearchProject).order_by(ResearchProject.started_day.desc())
    )).scalars().all()

    return [
        {
            "id": p.id,
            "merchant_ai": p.merchant_ai,
            "category": p.category,
            "product_name": p.product_name,
            "days_total": p.days_total,
            "days_remaining": p.days_remaining,
            "status": p.status,
            "started_day": p.started_day,
            "completed_day": p.completed_day,
        }
        for p in projects
    ]


@router.post("/admin/generate-strategies")
async def generate_strategies(db: AsyncSession = Depends(get_db)):
    from services.marketing_service import generate_all_strategies
    results = await generate_all_strategies(db)
    auto = sum(1 for r in results if r.get("status") == "auto_executed")
    pending = sum(1 for r in results if r.get("status") == "pending_approval")
    return {
        "results": results,
        "auto_executed": auto,
        "pending_approval": pending,
        "message": f"生成 {len(results)} 条策略：{auto} 条自动执行，{pending} 条待审批"
    }
