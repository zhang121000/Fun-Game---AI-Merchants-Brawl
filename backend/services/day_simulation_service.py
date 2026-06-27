"""Day-by-day simulation service."""

import asyncio
import random
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ai.provider_registry import get_provider
from config import get_settings
from constants import CATEGORY_DEMO_AFFINITY
from models.customer import Customer
from models.marketing import DailyDecision, PlatformAllocation, ProductIteration, ResearchProject, SimulationState
from models.order import Order, OrderItem
from models.product import Product


_API_KEY_MAP = {
    "GLM": lambda settings: settings.DEEPSEEK_API_KEY,
    "gpt": lambda settings: settings.GPT_API_KEY,
    "MiniMax": lambda settings: settings.DOUBAO_API_KEY,
    "Kimi": lambda settings: settings.DEEPSEEK_API_KEY,
    "qwen": lambda settings: settings.QWEN_API_KEY,
}


async def advance_day(db: AsyncSession, on_ai_complete=None) -> dict:
    """Advance the simulation by one day."""
    simulation_state = (await db.execute(select(SimulationState))).scalars().first()
    if not simulation_state:
        simulation_state = SimulationState(current_day=0)
        db.add(simulation_state)
        await db.flush()

    simulation_state.current_day += 1
    day = simulation_state.current_day

    from ai.graph_state import build_initial_day_state
    from ai.graphs.day_simulation_graph import run_day_simulation_graph

    graph_state = await run_day_simulation_graph(
        build_initial_day_state(day),
        db,
        on_ai_complete=on_ai_complete,
    )
    _apply_restock_decisions(graph_state)
    await _persist_day_results(db, graph_state)
    graph_state = await _run_post_day_processing(db, graph_state)
    await db.commit()
    return _build_advance_day_response(graph_state)


async def _persist_day_results(db: AsyncSession, graph_state: dict) -> None:
    for allocation in graph_state["traffic_allocations"]:
        db.add(
            PlatformAllocation(
                day=graph_state["day"],
                merchant_ai=allocation["merchant_ai"],
                demographic=allocation["demographic"],
                traffic_count=allocation.get("traffic", 0),
                reasoning=graph_state["platform_reasoning"],
            )
        )

    for row in graph_state["rankings"]:
        decision = graph_state["merchant_decisions"].get(row["merchant_ai"], {})
        product = graph_state["product_map"].get(row["merchant_ai"])
        fallback_price = float(product.price) if product else 0.0
        research = decision.get("research_new_product") or {}
        db.add(
            DailyDecision(
                day=graph_state["day"],
                merchant_ai=row["merchant_ai"],
                category=row["category"],
                product_name=row["product_name"],
                price=decision.get("price", fallback_price),
                promotion=decision.get("promotion", ""),
                target_focus=decision.get("target_focus", ""),
                description_update=decision.get("description_update", ""),
                reasoning=decision.get("reasoning", ""),
                traffic_received=row["traffic_received"],
                units_sold=row["units_sold"],
                revenue=row["revenue"],
                rank=row["rank"],
                research_product=research.get("name", ""),
                research_days_remaining=research.get("days_needed", 0),
            )
        )


async def _run_post_day_processing(db: AsyncSession, graph_state: dict) -> dict:
    await _process_research(db, graph_state["merchant_decisions"], graph_state["day"])
    graph_state["suggestions"] = await _check_platform_suggestions(
        db,
        graph_state["rankings"],
        graph_state["day"],
    )
    return graph_state


def _build_advance_day_response(graph_state: dict) -> dict:
    return {
        "day": graph_state["day"],
        "rankings": graph_state["rankings"],
        "platform_reasoning": graph_state["platform_reasoning"],
        "suggestions": graph_state["suggestions"],
        "total_orders": sum(row["units_sold"] for row in graph_state["rankings"]),
        "total_revenue": sum(row["revenue"] for row in graph_state["rankings"]),
        "execution_path": graph_state["execution_path"],
        "graph_version": graph_state["graph_version"],
        "halt_reason": graph_state["halt_reason"],
        "halted": graph_state.get("halted", False),
        "error_count": len(graph_state["errors"]),
        "recovered_error_count": graph_state.get("recovered_error_count", 0),
        "failed_merchants": graph_state.get("failed_merchants", []),
        "retry_summary": graph_state.get("retry_summary", {}),
        "execution_trace": graph_state["execution_trace"],
    }


def _apply_restock_decisions(graph_state: dict) -> None:
    if not graph_state.get("merchant_decisions"):
        return

    for ai_model, decision in graph_state["merchant_decisions"].items():
        restock = decision.get("restock", 0)
        if isinstance(restock, (int, float)) and restock > 0:
            product = graph_state["product_map"].get(ai_model)
            if product:
                product.stock = min(product.stock + int(restock), 99999)


async def _collect_merchant_performance(db, merchants, product_map, yesterday):
    del merchants
    results = []

    for ai_model, product in product_map.items():
        yesterday_query = await db.execute(
            select(
                func.coalesce(func.sum(OrderItem.quantity), 0),
                func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(OrderItem.product_id == product.id)
            .where(Order.simulated_day == yesterday)
        )
        yesterday_units, yesterday_revenue = yesterday_query.one()

        seven_day_query = await db.execute(
            select(func.coalesce(func.sum(OrderItem.quantity), 0))
            .join(Order, OrderItem.order_id == Order.id)
            .where(OrderItem.product_id == product.id)
            .where(Order.simulated_day > max(0, yesterday - 7))
            .where(Order.simulated_day <= yesterday)
        )
        total_7d = seven_day_query.scalar() or 0
        avg_7d = total_7d / 7 if yesterday > 0 else 0

        if yesterday_units > avg_7d * 1.1:
            trend = "up"
        elif yesterday_units < avg_7d * 0.9:
            trend = "down"
        else:
            trend = "flat"

        results.append(
            {
                "ai_model": ai_model,
                "merchant_name": product.merchant.name if product.merchant else "unknown",
                "category": product.category,
                "product_name": product.name,
                "yesterday_units": int(yesterday_units),
                "yesterday_revenue": float(yesterday_revenue),
                "avg_units_7d": float(avg_7d),
                "trend": trend,
                "stock": product.stock,
                "current_price": float(product.price),
                "original_price": float(product.original_price),
                "rank": 0,
            }
        )

    results.sort(key=lambda item: item["yesterday_units"], reverse=True)
    for index, row in enumerate(results, start=1):
        row["rank"] = index
    return results


async def _get_all_decisions(db, product_map, merchants_data, allocations, day, on_ai_complete=None):
    del db, product_map
    settings = get_settings()

    async def _get_decision(merchant_info):
        ai_model = merchant_info["ai_model"]
        api_key_fn = _API_KEY_MAP.get(ai_model)
        if not api_key_fn:
            return ai_model, {}

        api_key = api_key_fn(settings)
        if not api_key:
            return ai_model, {}

        my_traffic = sum(
            allocation.get("traffic", 0)
            for allocation in allocations
            if allocation["merchant_ai"] == ai_model
        )
        competitors = [
            f"rank {merchant['rank']}: {merchant['ai_model']} ({merchant['category']}) trend {merchant['trend']}"
            for merchant in merchants_data
            if merchant["ai_model"] != ai_model
        ]
        prompt = _build_merchant_prompt(merchant_info, my_traffic, competitors, day)

        provider = get_provider(ai_model, api_key=api_key)
        try:
            data = await asyncio.wait_for(
                provider.generate_structured(prompt, temperature=0.5),
                timeout=60.0,
            )
            result = data or {}
        except Exception as exc:
            print(f"{ai_model} decision failed: {exc}")
            result = {}

        if on_ai_complete:
            on_ai_complete(ai_model)
        return ai_model, result

    raw_results = await asyncio.gather(
        *[_get_decision(merchant_info) for merchant_info in merchants_data],
        return_exceptions=True,
    )

    decisions = {}
    for item in raw_results:
        if isinstance(item, Exception):
            continue
        ai_model, result = item
        decisions[ai_model] = result
    return decisions


def _build_merchant_prompt(merchant_info, my_traffic, competitors, day):
    return f"""You are an AI merchant operating the {merchant_info['category']} category.
Today is day {day}.

Your product:
- name: {merchant_info['product_name']}
- current price: {merchant_info['current_price']}
- original price: {merchant_info['original_price']}
- stock: {merchant_info['stock']}
- yesterday units: {merchant_info['yesterday_units']}
- yesterday revenue: {merchant_info['yesterday_revenue']:.0f}
- seven day avg: {merchant_info['avg_units_7d']:.1f}
- trend: {merchant_info['trend']}
- current rank: {merchant_info['rank']}

Traffic assigned today: about {my_traffic} shoppers.

Competitors:
{chr(10).join(competitors)}

Return JSON only:
{{
  "price": {merchant_info['current_price']},
  "promotion": "promotion text or empty string",
  "target_focus": "child|youth|middle|elderly",
  "description_update": "updated selling points or empty string",
  "restock": 0,
  "research_new_product": {{"name": "new product name", "description": "new product description", "price": 0, "days_needed": 3}} | null,
  "reasoning": "why you chose this plan"
}}

Notes:
- keep price changes within about 15 percent
- leaders may raise price modestly
- last place may cut price or start research
- restock should be 0 or between 1 and 99999
- research format: {{"name": "new name", "description": "new description", "price": 0, "days_needed": 3}}"""


async def _generate_orders(db, product_map, allocations, decisions, day):
    results = []
    all_customers = (await db.execute(select(Customer))).scalars().all()
    customers_by_demo = {}
    for customer in all_customers:
        customers_by_demo.setdefault(customer.demographic, []).append(customer)

    for ai_model, product in product_map.items():
        decision = decisions.get(ai_model, {})
        traffic_received = 0
        units_sold = 0
        revenue = 0.0
        my_allocations = [allocation for allocation in allocations if allocation["merchant_ai"] == ai_model]

        for allocation in my_allocations:
            demographic = allocation["demographic"]
            traffic = allocation.get("traffic", 0)
            traffic_received += traffic
            customers = customers_by_demo.get(demographic, [])
            if not customers:
                continue

            base_conversion = 0.15
            price = decision.get("price", float(product.price))
            price_factor = 1.0
            if float(product.original_price) > 0:
                discount = 1 - price / float(product.original_price)
                price_factor = 1 + discount * 2

            promo_factor = 1.3 if decision.get("promotion", "") else 1.0
            affinity = CATEGORY_DEMO_AFFINITY.get(product.category, {}).get(demographic, 0.5)
            conversion = min(base_conversion * price_factor * promo_factor * affinity, 0.6)
            actual_buyers = random.binomialvariate(traffic, conversion)

            for _ in range(actual_buyers):
                customer = random.choice(customers)
                quantity = 1 if random.random() < 0.75 else 2
                order = Order(
                    customer_id=customer.id,
                    merchant_id=product.merchant_id,
                    total_amount=price * quantity,
                    status="completed",
                    is_simulated=True,
                    simulated_day=day,
                )
                db.add(order)
                await db.flush()
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=price,
                    )
                )
                product.stock = max(0, product.stock - quantity)
                units_sold += quantity
                revenue += price * quantity

        results.append(
            {
                "merchant_ai": ai_model,
                "category": product.category,
                "product_name": product.name,
                "traffic_received": traffic_received,
                "units_sold": units_sold,
                "revenue": round(revenue, 2),
                "rank": 0,
            }
        )

    return results


async def _process_research(db, decisions, day):
    for ai_model, decision in decisions.items():
        research = decision.get("research_new_product")
        if research and isinstance(research, dict):
            name = research.get("name", "")
            days = research.get("days_needed", 3)
            if name:
                existing = (
                    await db.execute(
                        select(ResearchProject)
                        .where(ResearchProject.merchant_ai == ai_model)
                        .where(ResearchProject.status == "active")
                    )
                ).scalars().first()
                if not existing:
                    db.add(
                        ResearchProject(
                            merchant_ai=ai_model,
                            category=decision.get("category", ""),
                            product_name=name,
                            new_description=research.get("description", ""),
                            new_price=research.get("price", 0.0),
                            days_total=days,
                            days_remaining=days,
                            status="active",
                            started_day=day,
                        )
                    )

    active_projects = (
        await db.execute(select(ResearchProject).where(ResearchProject.status == "active"))
    ).scalars().all()

    for project in active_projects:
        project.days_remaining -= 1
        if project.days_remaining <= 0:
            project.status = "completed"
            project.completed_day = day
            product = (
                await db.execute(select(Product).where(Product.ai_model == project.merchant_ai))
            ).scalars().first()
            if product:
                db.add(
                    ProductIteration(
                        merchant_ai=project.merchant_ai,
                        day=day,
                        old_name=product.name,
                        new_name=project.product_name,
                        old_description=product.description,
                        new_description=project.new_description,
                        old_price=float(product.price),
                        new_price=project.new_price,
                    )
                )
                product.name = project.product_name
                product.description = project.new_description
                product.price = project.new_price
                product.original_price = project.new_price


async def _check_platform_suggestions(db, rankings, day):
    suggestions = []
    if len(rankings) < 2:
        return suggestions

    last_place = rankings[-1]
    ai_model = last_place["merchant_ai"]
    recent_decisions = (
        await db.execute(
            select(DailyDecision)
            .where(DailyDecision.merchant_ai == ai_model)
            .where(DailyDecision.day >= day - 2)
            .where(DailyDecision.day < day)
            .order_by(DailyDecision.day.desc())
        )
    ).scalars().all()

    consecutive_last = all(decision.rank == len(rankings) for decision in recent_decisions)
    if consecutive_last and len(recent_decisions) >= 1:
        suggestions.append(
            {
                "merchant_ai": ai_model,
                "type": "warning",
                "message": f"{ai_model} in {last_place['category']} has been last for {len(recent_decisions) + 1} days.",
            }
        )

    for row in rankings:
        if row["units_sold"] == 0 and row["traffic_received"] > 10:
            suggestions.append(
                {
                    "merchant_ai": row["merchant_ai"],
                    "type": "alert",
                    "message": f"{row['merchant_ai']} got {row['traffic_received']} visits but sold nothing.",
                }
            )

    return suggestions

