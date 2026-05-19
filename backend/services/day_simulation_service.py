"""日期推进模拟服务"""

import asyncio
import random
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.merchant import Merchant
from models.product import Product
from models.customer import Customer
from models.order import Order, OrderItem
from models.marketing import (
    SimulationState, DailyDecision, PlatformAllocation,
    ResearchProject, ProductIteration,
)
from services.platform_ai_service import allocate_customers
from ai.provider_registry import get_provider
from config import get_settings
from constants import CATEGORY_DEMO_AFFINITY, DEMOGRAPHIC_RATIO


_API_KEY_MAP = {
    "GLM":      lambda s: s.DEEPSEEK_API_KEY,
    "gpt":      lambda s: s.GPT_API_KEY,
    "MiniMax":  lambda s: s.DOUBAO_API_KEY,
    "Kimi":     lambda s: s.DEEPSEEK_API_KEY,
    "qwen":     lambda s: s.QWEN_API_KEY,
}


async def advance_day(db: AsyncSession, on_ai_complete=None) -> dict:
    """推进一天：平台分配 → 商家决策 → 生成订单 → 更新排名"""

    # 1. 获取/创建模拟状态
    state = (await db.execute(select(SimulationState))).scalars().first()
    if not state:
        state = SimulationState(current_day=0)
        db.add(state)
        await db.flush()

    state.current_day += 1
    day = state.current_day

    # 2. 收集商家数据
    merchants = (await db.execute(select(Merchant))).scalars().all()
    products = (await db.execute(
        select(Product).where(Product.is_active == True)
    )).scalars().all()

    # 按AI模型分组产品（每个AI一个品类）
    product_map = {}
    for p in products:
        product_map[p.ai_model] = p

    # 3. 收集昨日表现数据（直接使用 product_map）
    yesterday = day - 1
    merchants_data = await _collect_merchant_performance(db, None, product_map, yesterday)

    # 4. 平台AI分配顾客流量
    try:
        print(f"🔄 调用平台AI分配顾客 (第{day}天)...")
        allocation_result = await asyncio.wait_for(
            allocate_customers(merchants_data, day),
            timeout=15.0,  # 减少到15秒
        )
        print(f"✅ 平台AI分配成功，获得 {len(allocation_result.get('allocations', []))} 条分配")
    except (asyncio.TimeoutError, Exception) as e:
        print(f"⚠️ 平台AI分配失败: {type(e).__name__}: {e}，使用降级方案")
        from services.platform_ai_service import _fallback_allocate
        settings = get_settings()
        allocation_result = _fallback_allocate(merchants_data, settings.DEFAULT_TRAFFIC_POOL)

    allocations = allocation_result.get("allocations", [])
    platform_reasoning = allocation_result.get("reasoning", "")

    # 5. 记录平台分配
    for alloc in allocations:
        db.add(PlatformAllocation(
            day=day,
            merchant_ai=alloc["merchant_ai"],
            demographic=alloc["demographic"],
            traffic_count=alloc.get("traffic", 0),
            reasoning=platform_reasoning,
        ))

    # 6. 5个商家AI并行决策
    decisions = await _get_all_decisions(db, product_map, merchants_data, allocations, day, on_ai_complete)

    # 6.5 执行进货决策
    for ai_model, decision in decisions.items():
        restock = decision.get("restock", 0)
        if isinstance(restock, (int, float)) and restock > 0:
            product = product_map.get(ai_model)
            if product:
                product.stock = min(product.stock + int(restock), 99999)

    # 7. 概率引擎生成订单
    orders_result = await _generate_orders(db, product_map, allocations, decisions, day)

    # 8. 计算排名
    rankings = sorted(
        orders_result,
        key=lambda x: x["units_sold"],
        reverse=True,
    )
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    # 9. 记录决策日志
    for r in rankings:
        decision = decisions.get(r["merchant_ai"], {})
        product = product_map.get(r["merchant_ai"])
        fallback_price = float(product.price) if product else 0.0
        db.add(DailyDecision(
            day=day,
            merchant_ai=r["merchant_ai"],
            category=r["category"],
            product_name=r["product_name"],
            price=decision.get("price", fallback_price),
            promotion=decision.get("promotion", ""),
            target_focus=decision.get("target_focus", ""),
            description_update=decision.get("description_update", ""),
            reasoning=decision.get("reasoning", ""),
            traffic_received=r["traffic_received"],
            units_sold=r["units_sold"],
            revenue=r["revenue"],
            rank=r["rank"],
            research_product=decision.get("research_new_product", {}).get("name", "") if decision.get("research_new_product") else "",
            research_days_remaining=decision.get("research_new_product", {}).get("days_needed", 0) if decision.get("research_new_product") else 0,
        ))

    # 10. 处理研发项目
    await _process_research(db, decisions, day)

    # 11. 检查平台建议
    suggestions = await _check_platform_suggestions(db, rankings, day)

    await db.commit()

    return {
        "day": day,
        "rankings": rankings,
        "platform_reasoning": platform_reasoning,
        "suggestions": suggestions,
        "total_orders": sum(r["units_sold"] for r in rankings),
        "total_revenue": sum(r["revenue"] for r in rankings),
    }


async def _collect_merchant_performance(db, merchants, product_map, yesterday):
    """收集各商家的表现数据"""
    result = []

    # 直接遍历产品，每个产品对应一个AI商家
    for ai_model, product in product_map.items():
        # 昨日销量
        yesterday_q = await db.execute(
            select(
                func.coalesce(func.sum(OrderItem.quantity), 0),
                func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(OrderItem.product_id == product.id)
            .where(Order.simulated_day == yesterday)
        )
        y_units, y_revenue = yesterday_q.one()

        # 7天平均（简化查询）
        seven_day_q = await db.execute(
            select(
                func.coalesce(func.sum(OrderItem.quantity), 0),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .where(OrderItem.product_id == product.id)
            .where(Order.simulated_day > max(0, yesterday - 7))
            .where(Order.simulated_day <= yesterday)
        )
        total_7d = seven_day_q.scalar() or 0
        avg_7d = total_7d / 7 if yesterday > 0 else 0

        # 趋势
        if y_units > avg_7d * 1.1:
            trend = "↑ 上升"
        elif y_units < avg_7d * 0.9:
            trend = "↓ 下降"
        else:
            trend = "→ 平稳"

        result.append({
            "ai_model": ai_model,
            "merchant_name": product.merchant.name if product.merchant else "未知商家",
            "category": product.category,
            "product_name": product.name,
            "yesterday_units": int(y_units),
            "yesterday_revenue": float(y_revenue),
            "avg_units_7d": float(avg_7d),
            "trend": trend,
            "stock": product.stock,
            "current_price": float(product.price),
            "original_price": float(product.original_price),
            "rank": 0,  # 后面计算
        })

    # 计算排名
    result.sort(key=lambda x: x["yesterday_units"], reverse=True)
    for i, r in enumerate(result):
        r["rank"] = i + 1

    return result


async def _get_all_decisions(db, product_map, merchants_data, allocations, day, on_ai_complete=None):
    """并行获取5个商家AI的决策"""
    settings = get_settings()

    async def _get_decision(merchant_info):
        ai_model = merchant_info["ai_model"]
        api_key_fn = _API_KEY_MAP.get(ai_model)
        if not api_key_fn:
            return ai_model, {}
        api_key = api_key_fn(settings)
        if not api_key:
            return ai_model, {}

        # 计算该商家今天获得的总流量
        my_traffic = sum(
            a.get("traffic", 0)
            for a in allocations
            if a["merchant_ai"] == ai_model
        )

        # 查看竞争对手排名（不含具体数据）
        competitors = [
            f"第{m['rank']}名: {m['ai_model']}({m['category']}) 趋势{m['trend']}"
            for m in merchants_data
            if m["ai_model"] != ai_model
        ]

        prompt = _build_merchant_prompt(
            merchant_info, my_traffic, competitors, day
        )

        provider = get_provider(ai_model, api_key=api_key)
        try:
            data = await asyncio.wait_for(
                provider.generate_structured(prompt, temperature=0.5),
                timeout=60.0,
            )
            result = data or {}
        except Exception as e:
            import traceback
            print(f"⚠️ {ai_model} 决策失败 [{type(e).__name__}]: {e}")
            traceback.print_exc()
            result = {}

        # 通知外部该AI已完成
        if on_ai_complete:
            on_ai_complete(ai_model)
        return ai_model, result

    tasks = [_get_decision(m) for m in merchants_data]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    decisions = {}
    for item in raw_results:
        if isinstance(item, Exception):
            continue
        ai_model, result = item
        decisions[ai_model] = result

    return decisions


def _build_merchant_prompt(merchant_info, my_traffic, competitors, day):
    """构建商家AI的决策提示词"""
    return f"""你是保健品电商平台上的AI商家，负责经营「{merchant_info['category']}」品类。
今天是第{day}天。

【你的产品】
- 名称：{merchant_info['product_name']}
- 当前售价：¥{merchant_info['current_price']}（原价 ¥{merchant_info['original_price']}）
- 库存：{merchant_info['stock']}件
- 昨日销量：{merchant_info['yesterday_units']}件
- 昨日收入：¥{merchant_info['yesterday_revenue']:.0f}
- 7天平均：{merchant_info['avg_units_7d']:.1f}件/天
- 趋势：{merchant_info['trend']}
- 当前排名：第{merchant_info['rank']}名

【今日平台分配给你的流量】约{my_traffic}个潜在顾客会看到你的产品

【竞争对手排名】
{chr(10).join(competitors)}

【你需要决定】
1. 今天的产品定价（可以调价，但幅度别太大）
2. 今天是否做促销活动（如满减、折扣、买赠）
3. 今天重点 targeting 哪个人群（child/youth/middle/elderly）
4. 是否要更新产品描述/卖点
5. 如果库存不足，可以进货（1~99999件）
6. 如果排名垫底，可以启动研发新品（需指定名称、描述、售价、所需天数）

请严格输出以下 JSON 格式（不要输出其他任何内容）：
{{
  "price": {merchant_info['current_price']},
  "promotion": "促销方案描述，或空字符串表示不促销",
  "target_focus": "child|youth|middle|elderly",
  "description_update": "新的卖点描述，或空字符串表示不更新",
  "restock": 0,
  "research_new_product": {{"name": "新品名称（必填，如'有机综合维生素矿物质片'）", "description": "新品描述（必填）", "price": 新品售价（必填，数字）, "days_needed": 研发所需天数（必填，1~7）}} | 不研发填 null,
  "reasoning": "你的决策理由"
}}

注意：
- 价格调整幅度建议在±15%以内
- 如果排名靠前，可以适当提价
- 如果排名垫底，考虑降价或研发新品
- 库存不足时可以设置restock数量（1~99999），不进货则填0
- 研发新品格式：{{"name": "新品名", "description": "新品描述", "price": 新品售价, "days_needed": 3}}"""


async def _generate_orders(db, product_map, allocations, decisions, day):
    """概率引擎：根据平台分配和商家决策生成订单"""
    results = []

    # 预加载顾客
    all_customers = (await db.execute(select(Customer))).scalars().all()
    customers_by_demo = {}
    for c in all_customers:
        customers_by_demo.setdefault(c.demographic, []).append(c)

    for ai_model, product in product_map.items():
        decision = decisions.get(ai_model, {})
        traffic_received = 0
        units_sold = 0
        revenue = 0.0

        # 获取该商家今天获得的各人群流量
        my_allocations = [
            a for a in allocations if a["merchant_ai"] == ai_model
        ]

        for alloc in my_allocations:
            demo = alloc["demographic"]
            traffic = alloc.get("traffic", 0)
            traffic_received += traffic

            # 获取该人群的顾客
            customers = customers_by_demo.get(demo, [])
            if not customers:
                continue

            # 计算转化率
            base_conversion = 0.15  # 基础转化率15%

            # 价格因素：比原价低→转化率高
            price = decision.get("price", float(product.price))
            price_factor = 1.0
            if float(product.original_price) > 0:
                discount = 1 - price / float(product.original_price)
                price_factor = 1 + discount * 2  # 打9折→转化率+20%

            # 促销因素
            promo = decision.get("promotion", "")
            promo_factor = 1.3 if promo else 1.0

            # 品类-人群匹配度
            affinity = CATEGORY_DEMO_AFFINITY.get(
                product.category, {}
            ).get(demo, 0.5)

            # 最终转化率
            conversion = base_conversion * price_factor * promo_factor * affinity
            conversion = min(conversion, 0.6)  # 上限60%

            # 生成订单
            actual_buyers = 0
            for _ in range(traffic):
                if random.random() < conversion:
                    actual_buyers += 1

            # 为每个买家创建订单
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

                db.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=price,
                ))

                product.stock = max(0, product.stock - quantity)
                units_sold += quantity
                revenue += price * quantity

        results.append({
            "merchant_ai": ai_model,
            "category": product.category,
            "product_name": product.name,
            "traffic_received": traffic_received,
            "units_sold": units_sold,
            "revenue": round(revenue, 2),
            "rank": 0,
        })

    return results


async def _process_research(db, decisions, day):
    """处理研发项目"""
    # 检查是否有新的研发请求
    for ai_model, decision in decisions.items():
        research = decision.get("research_new_product")
        if research and isinstance(research, dict):
            name = research.get("name", "")
            days = research.get("days_needed", 3)
            if name:
                # 检查是否已有进行中的研发
                existing = (await db.execute(
                    select(ResearchProject)
                    .where(ResearchProject.merchant_ai == ai_model)
                    .where(ResearchProject.status == "active")
                )).scalars().first()

                if not existing:
                    db.add(ResearchProject(
                        merchant_ai=ai_model,
                        category=decision.get("category", ""),
                        product_name=name,
                        new_description=research.get("description", ""),
                        new_price=research.get("price", 0.0),
                        days_total=days,
                        days_remaining=days,
                        status="active",
                        started_day=day,
                    ))

    # 推进进行中的研发
    active_projects = (await db.execute(
        select(ResearchProject).where(ResearchProject.status == "active")
    )).scalars().all()

    for project in active_projects:
        project.days_remaining -= 1
        if project.days_remaining <= 0:
            project.status = "completed"
            project.completed_day = day

            # 查找该 AI 商家对应的产品
            product_result = (await db.execute(
                select(Product)
                .where(Product.ai_model == project.merchant_ai)
            )).scalars().first()

            if product_result:
                # 记录迭代快照
                db.add(ProductIteration(
                    merchant_ai=project.merchant_ai,
                    day=day,
                    old_name=product_result.name,
                    new_name=project.product_name,
                    old_description=product_result.description,
                    new_description=project.new_description,
                    old_price=float(product_result.price),
                    new_price=project.new_price,
                ))
                # 更新产品
                product_result.name = project.product_name
                product_result.description = project.new_description
                product_result.price = project.new_price
                product_result.original_price = project.new_price


async def _check_platform_suggestions(db, rankings, day):
    """检查是否需要发送平台建议"""
    suggestions = []

    if len(rankings) < 2:
        return suggestions

    # 检查连续垫底
    last_place = rankings[-1]
    ai_model = last_place["merchant_ai"]

    # 查最近2天的排名
    recent_decisions = (await db.execute(
        select(DailyDecision)
        .where(DailyDecision.merchant_ai == ai_model)
        .where(DailyDecision.day >= day - 2)
        .where(DailyDecision.day < day)
        .order_by(DailyDecision.day.desc())
    )).scalars().all()

    consecutive_last = all(d.rank == len(rankings) for d in recent_decisions)

    if consecutive_last and len(recent_decisions) >= 1:
        suggestions.append({
            "merchant_ai": ai_model,
            "type": "warning",
            "message": f"⚠️ {ai_model}（{last_place['category']}）连续{len(recent_decisions)+1}天排名垫底，建议：调整营销策略或研发新品",
        })

    # 检查销量大幅下滑
    for r in rankings:
        if r["units_sold"] == 0 and r["traffic_received"] > 10:
            suggestions.append({
                "merchant_ai": r["merchant_ai"],
                "type": "alert",
                "message": f"🚨 {r['merchant_ai']}（{r['category']}）今日零销量但有{r['traffic_received']}个流量，转化率为0，请立即调整策略",
            })

    return suggestions
