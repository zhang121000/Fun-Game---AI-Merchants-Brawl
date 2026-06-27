import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session, get_db
from models.customer import Customer
from models.marketing import DailyDecision, MarketingStrategy, PlatformAllocation, ProductIteration, ResearchProject, SimulationState
from models.merchant import Merchant
from models.order import Order
from models.product import Product

router = APIRouter()

_simulation_lock = asyncio.Lock()
_simulation_status = {
    "running": False,
    "day": 0,
    "result": None,
    "error": None,
    "ai_completed": [],
    "execution_path": None,
    "graph_version": None,
    "halt_reason": None,
    "error_count": 0,
    "halted": False,
    "recovered_error_count": 0,
    "failed_merchants": [],
    "retry_summary": {},
}


@router.get("/admin/overview")
async def admin_overview(db: AsyncSession = Depends(get_db)):
    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar() or 0
    total_revenue = (await db.execute(select(func.coalesce(func.sum(Order.total_amount), 0)))).scalar() or 0
    total_merchants = (await db.execute(select(func.count()).select_from(Merchant))).scalar() or 0
    total_customers = (await db.execute(select(func.count()).select_from(Customer))).scalar() or 0
    total_products = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0

    state = (await db.execute(select(SimulationState))).scalars().first()
    current_day = state.current_day if state else 0

    pending_strategies = (
        await db.execute(
            select(func.count()).select_from(MarketingStrategy).where(MarketingStrategy.status == "pending")
        )
    ).scalar() or 0

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
    global _simulation_status

    if _simulation_status["running"]:
        return {
            "status": "running",
            "message": f"Simulation already running for day {_simulation_status['day']}",
            "day": _simulation_status["day"],
        }

    state = (await db.execute(select(SimulationState))).scalars().first()
    next_day = (state.current_day if state else 0) + 1

    _simulation_status = {
        "running": True,
        "day": next_day,
        "result": None,
        "error": None,
        "ai_completed": [],
        "execution_path": None,
        "graph_version": None,
        "halt_reason": None,
        "error_count": 0,
        "halted": False,
        "recovered_error_count": 0,
        "failed_merchants": [],
        "retry_summary": {},
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
                    "execution_path": result.get("execution_path"),
                    "graph_version": result.get("graph_version"),
                    "halt_reason": result.get("halt_reason"),
                    "error_count": result.get("error_count", 0),
                    "halted": result.get("halted", False),
                    "recovered_error_count": result.get("recovered_error_count", 0),
                    "failed_merchants": result.get("failed_merchants", []),
                    "retry_summary": result.get("retry_summary", {}),
                }
        except Exception as exc:
            _simulation_status = {
                "running": False,
                "day": next_day,
                "result": None,
                "error": str(exc),
                "ai_completed": _simulation_status.get("ai_completed", []),
                "execution_path": None,
                "graph_version": None,
                "halt_reason": None,
                "error_count": 0,
                "halted": False,
                "recovered_error_count": 0,
                "failed_merchants": [],
                "retry_summary": {},
            }

    background_tasks.add_task(_run_simulation)

    return {
        "status": "started",
        "day": next_day,
        "message": f"Day {next_day} simulation started.",
    }


@router.get("/admin/advance-day-status")
async def advance_day_status():
    return _simulation_status


class RestockBody(BaseModel):
    amount: int


@router.post("/admin/products/{product_id}/restock")
async def admin_restock(product_id: int, body: RestockBody, db: AsyncSession = Depends(get_db)):
    amount = body.amount
    if amount < 1 or amount > 99999:
        return {"error": "Restock amount must be between 1 and 99999"}

    product = await db.get(Product, product_id)
    if not product:
        return {"error": "Product not found"}

    product.stock = min(product.stock + amount, 99999)
    await db.commit()
    return {"product_id": product_id, "stock": product.stock, "added": amount}


@router.post("/admin/reset")
async def admin_reset(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    from models.order import OrderItem

    await db.execute(delete(OrderItem))
    await db.execute(delete(Order))
    await db.execute(delete(DailyDecision))
    await db.execute(delete(PlatformAllocation))
    await db.execute(delete(ResearchProject))
    await db.execute(delete(ProductIteration))
    await db.execute(delete(SimulationState))

    products = (await db.execute(select(Product))).scalars().all()
    for product in products:
        product.stock = 200

    db.add(SimulationState(current_day=0))

    global _simulation_status
    _simulation_status = {
        "running": False,
        "day": 0,
        "result": None,
        "error": None,
        "ai_completed": [],
        "execution_path": None,
        "graph_version": None,
        "halt_reason": None,
        "error_count": 0,
        "halted": False,
        "recovered_error_count": 0,
        "failed_merchants": [],
        "retry_summary": {},
    }

    await db.commit()
    return {"status": "ok", "message": "Simulation reset complete"}


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
    state = (await db.execute(select(SimulationState))).scalars().first()
    if not state or state.current_day == 0:
        return {"day": 0, "rankings": []}

    current_day = state.current_day
    decisions = (
        await db.execute(
            select(DailyDecision).where(DailyDecision.day == current_day).order_by(DailyDecision.rank)
        )
    ).scalars().all()

    rankings = []
    for decision in decisions:
        history = (
            await db.execute(
                select(DailyDecision.rank, DailyDecision.units_sold)
                .where(DailyDecision.merchant_ai == decision.merchant_ai)
                .where(DailyDecision.day >= max(1, current_day - 7))
                .where(DailyDecision.day <= current_day)
                .order_by(DailyDecision.day)
            )
        ).all()

        rankings.append(
            {
                "merchant_ai": decision.merchant_ai,
                "category": decision.category,
                "product_name": decision.product_name,
                "rank": decision.rank,
                "units_sold": decision.units_sold,
                "revenue": decision.revenue,
                "price": decision.price,
                "promotion": decision.promotion,
                "target_focus": decision.target_focus,
                "reasoning": decision.reasoning,
                "traffic_received": decision.traffic_received,
                "history": [{"rank": item[0], "units": item[1]} for item in history],
            }
        )

    return {"day": current_day, "rankings": rankings}


@router.get("/admin/decision-log")
async def decision_log(day: int = Query(None), db: AsyncSession = Depends(get_db)):
    if day is None:
        state = (await db.execute(select(SimulationState))).scalars().first()
        day = state.current_day if state else 1

    decisions = (
        await db.execute(select(DailyDecision).where(DailyDecision.day == day).order_by(DailyDecision.rank))
    ).scalars().all()
    allocations = (
        await db.execute(select(PlatformAllocation).where(PlatformAllocation.day == day))
    ).scalars().all()

    return {
        "day": day,
        "decisions": [
            {
                "merchant_ai": decision.merchant_ai,
                "category": decision.category,
                "product_name": decision.product_name,
                "price": decision.price,
                "promotion": decision.promotion,
                "target_focus": decision.target_focus,
                "description_update": decision.description_update,
                "reasoning": decision.reasoning,
                "traffic_received": decision.traffic_received,
                "units_sold": decision.units_sold,
                "revenue": decision.revenue,
                "rank": decision.rank,
                "research_product": decision.research_product,
            }
            for decision in decisions
        ],
        "allocations": [
            {
                "merchant_ai": allocation.merchant_ai,
                "demographic": allocation.demographic,
                "traffic_count": allocation.traffic_count,
            }
            for allocation in allocations
        ],
    }


@router.get("/admin/platform-suggestions")
async def platform_suggestions(db: AsyncSession = Depends(get_db)):
    state = (await db.execute(select(SimulationState))).scalars().first()
    if not state or state.current_day == 0:
        return {"suggestions": []}

    current_day = state.current_day
    decisions = (
        await db.execute(
            select(DailyDecision).where(DailyDecision.day == current_day).order_by(DailyDecision.rank)
        )
    ).scalars().all()

    if len(decisions) < 2:
        return {"suggestions": []}

    suggestions = []
    last = decisions[-1]
    recent = (
        await db.execute(
            select(DailyDecision)
            .where(DailyDecision.merchant_ai == last.merchant_ai)
            .where(DailyDecision.day >= current_day - 3)
            .where(DailyDecision.day < current_day)
            .order_by(DailyDecision.day.desc())
        )
    ).scalars().all()

    total_merchants = len(decisions)
    consecutive_last = all(item.rank == total_merchants for item in recent)
    if consecutive_last and len(recent) >= 1:
        suggestions.append(
            {
                "merchant_ai": last.merchant_ai,
                "category": last.category,
                "type": "warning",
                "message": f"Last place streak: {len(recent) + 1} days",
                "advice": "Consider price changes, promotions, or a new research project.",
            }
        )

    for decision in decisions:
        if decision.units_sold == 0 and decision.traffic_received > 10:
            suggestions.append(
                {
                    "merchant_ai": decision.merchant_ai,
                    "category": decision.category,
                    "type": "alert",
                    "message": f"Zero sales after {decision.traffic_received} visits.",
                    "advice": "Review pricing and product description.",
                }
            )

    active_research = (
        await db.execute(select(ResearchProject).where(ResearchProject.status == "active"))
    ).scalars().all()
    for research in active_research:
        suggestions.append(
            {
                "merchant_ai": research.merchant_ai,
                "category": research.category,
                "type": "info",
                "message": f"Research in progress for {research.product_name}, {research.days_remaining} days remaining.",
                "advice": "",
            }
        )

    return {"suggestions": suggestions}


@router.get("/admin/research-projects")
async def research_projects(db: AsyncSession = Depends(get_db)):
    projects = (
        await db.execute(select(ResearchProject).order_by(ResearchProject.started_day.desc()))
    ).scalars().all()

    return [
        {
            "id": project.id,
            "merchant_ai": project.merchant_ai,
            "category": project.category,
            "product_name": project.product_name,
            "days_total": project.days_total,
            "days_remaining": project.days_remaining,
            "status": project.status,
            "started_day": project.started_day,
            "completed_day": project.completed_day,
        }
        for project in projects
    ]


@router.post("/admin/generate-strategies")
async def generate_strategies(db: AsyncSession = Depends(get_db)):
    from services.marketing_service import generate_all_strategies

    results = await generate_all_strategies(db)
    auto = sum(1 for item in results if item.get("status") == "auto_executed")
    pending = sum(1 for item in results if item.get("status") == "pending_approval")
    return {
        "results": results,
        "auto_executed": auto,
        "pending_approval": pending,
        "message": f"Generated {len(results)} strategies: {auto} auto, {pending} pending.",
    }


@router.get("/admin/product-iterations")
async def product_iterations(
    merchant_ai: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    iterations = (
        await db.execute(
            select(ProductIteration)
            .where(ProductIteration.merchant_ai == merchant_ai)
            .order_by(ProductIteration.day.desc())
        )
    ).scalars().all()

    return [
        {
            "id": iteration.id,
            "merchant_ai": iteration.merchant_ai,
            "day": iteration.day,
            "old_name": iteration.old_name,
            "new_name": iteration.new_name,
            "old_description": iteration.old_description,
            "new_description": iteration.new_description,
            "old_price": iteration.old_price,
            "new_price": iteration.new_price,
        }
        for iteration in iterations
    ]
