"""营销策略生成服务（每产品独立 AI 控制）"""

from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ai.provider_registry import get_provider
from ai.prompts.marketing_strategist import build_strategy_prompt
from models.product import Product
from models.order import Order, OrderItem
from models.marketing import MarketingStrategy, StrategyStatus
from models.customer import Customer
from config import get_settings


_API_KEY_MAP = {
    "GLM":      lambda s: s.DEEPSEEK_API_KEY,
    "gpt":      lambda s: s.GPT_API_KEY,
    "MiniMax":  lambda s: s.DOUBAO_API_KEY,
    "Kimi":     lambda s: s.DEEPSEEK_API_KEY,
    "qwen":     lambda s: s.QWEN_API_KEY,
}

AUTO_PRICE_THRESHOLD = 0.10  # ±10%以内自动执行


async def generate_all_strategies(db: AsyncSession) -> list[dict]:
    """并行为每个产品生成营销策略"""
    import asyncio
    settings = get_settings()
    products = (await db.execute(
        select(Product).where(Product.is_active == True)
    )).scalars().all()

    results = []

    async def _generate_with_timeout(product):
        try:
            result = await asyncio.wait_for(
                _generate_for_product(db, product, settings),
                timeout=60.0
            )
            return result
        except asyncio.TimeoutError:
            return {"product": product.name, "ai": product.ai_model, "status": "error", "error": "AI 生成超时（60秒）"}
        except Exception as e:
            return {"product": product.name, "ai": product.ai_model, "status": "error", "error": str(e)}

    for product in products:
        try:
            result = await _generate_with_timeout(product)
            results.append(result)
        except Exception as e:
            print(f"⚠️ 产品 {product.name} (AI: {product.ai_model}) 策略生成失败: {e}")
            results.append({"product": product.name, "ai": product.ai_model, "status": "error", "error": str(e)})

    await db.commit()
    return results


async def _generate_for_product(db: AsyncSession, product: Product, settings) -> dict:
    api_key_fn = _API_KEY_MAP.get(product.ai_model)
    if not api_key_fn:
        return {"product": product.name, "ai": product.ai_model, "status": "skipped", "reason": "未知AI模型"}
    api_key = api_key_fn(settings)
    if not api_key:
        return {"product": product.name, "ai": product.ai_model, "status": "skipped", "reason": "API Key为空"}

    # 收集该产品的销售数据
    sales_data = await _collect_product_sales(db, product)

    # 构建 prompt（针对单个产品）
    prompt = _build_product_strategy_prompt(product, sales_data)

    provider = get_provider(product.ai_model, api_key=api_key)
    data = await provider.generate_structured(prompt, temperature=0.4)
    print(f"🔍 {product.name} ({product.ai_model}): generate_structured 返回 type={type(data).__name__}, has_get={hasattr(data, 'get') if data else 'N/A'}")
    if data and not isinstance(data, dict):
        print(f"⚠️ 期望 dict，实际收到: {repr(data)[:300]}")
    if not data:
        return {"product": product.name, "ai": product.ai_model, "status": "failed", "reason": "AI返回无效"}

    strategy_type = data.get("strategy_type", "recommendation_update")
    needs_approval = _check_needs_approval(data, product)

    strategy = MarketingStrategy(
        merchant_id=product.merchant_id,
        strategy_type=strategy_type,
        title=data.get("title", "未命名策略"),
        description=data.get("description", ""),
        proposed_changes=data.get("proposed_changes", {}),
        ai_reasoning=data.get("reasoning", ""),
        status=StrategyStatus.pending.value if needs_approval else StrategyStatus.approved.value,
    )
    db.add(strategy)
    await db.flush()

    # 记录到产品的 AI 策略历史
    history = product.ai_strategy_history or []
    history.append({
        "time": datetime.utcnow().isoformat(),
        "strategy_type": strategy_type,
        "title": data.get("title", ""),
        "auto_executed": not needs_approval,
    })
    # 只保留最近 20 条
    product.ai_strategy_history = history[-20:]

    result = {
        "product": product.name,
        "ai": product.ai_model,
        "strategy": data.get("title"),
        "type": strategy_type,
    }

    if not needs_approval:
        await _execute_product_strategy(product, data)
        result["status"] = "auto_executed"
        result["message"] = "小幅调整，已自动执行"
    else:
        result["status"] = "pending_approval"
        result["message"] = "大幅变更，等待管理员审批"

    return result


async def _collect_product_sales(db: AsyncSession, product: Product) -> dict:
    """收集单个产品的销售数据，包括人群分布"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    # 该产品 7 天内订单数和销售额
    stats_q = await db.execute(
        select(
            func.count(OrderItem.id),
            func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0),
            func.coalesce(func.sum(OrderItem.quantity), 0),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItem.product_id == product.id)
        .where(Order.created_at >= seven_days_ago)
    )
    orders_7d, revenue_7d, units_7d = stats_q.one()

    # 人群购买分布
    demo_q = await db.execute(
        select(
            Customer.demographic,
            func.count(OrderItem.id),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .where(OrderItem.product_id == product.id)
        .where(Order.created_at >= seven_days_ago)
        .group_by(Customer.demographic)
    )
    demo_breakdown = {r[0]: r[1] for r in demo_q.all()}

    return {
        "orders_7d": orders_7d,
        "revenue_7d": float(revenue_7d),
        "units_7d": int(units_7d),
        "demographic_breakdown": demo_breakdown,
        "current_price": float(product.price),
        "original_price": float(product.original_price),
        "stock": product.stock,
    }


def _build_product_strategy_prompt(product: Product, sales: dict) -> str:
    """为单个产品的 AI 构建策略提示词"""
    import random
    # 随机倾斜策略类型，增加多样性
    weights = random.random()
    if weights < 0.35:
        hint = "本次建议侧重【调价策略】，分析是否需要调整售价。"
    elif weights < 0.65:
        hint = "本次建议侧重【促销活动】，设计限时折扣或满减活动。"
    else:
        hint = "本次建议侧重【产品描述优化】，更新卖点和推荐语。"

    return f"""你是保健品「{product.name}」的专属AI营销专家。
产品类别：{product.category}
当前售价：¥{product.price}（原价 ¥{product.original_price}）
当前库存：{product.stock}
当前卖点：{product.ai_selling_points or ['暂无']}

【近7天销售数据】
- 订单数：{sales['orders_7d']}
- 销售额：¥{sales['revenue_7d']:.0f}
- 销量：{sales['units_7d']}件
- 人群购买分布：{sales['demographic_breakdown']}

{hint}

请基于数据分析，生成一条营销策略调整建议。
可选策略类型：
- price_adjustment：调价（幅度控制在±10%以内）
- promotion：促销活动（限时折扣、满减等）
- recommendation_update：更新产品描述和卖点

请严格输出以下 JSON 格式（不要输出其他任何内容）：
{{
  "strategy_type": "price_adjustment|promotion|recommendation_update",
  "title": "策略标题（简短，15字以内）",
  "description": "详细说明",
  "proposed_changes": {{
    "target_field": "变更的字段",
    "old_value": "旧值",
    "new_value": "新值"
  }},
  "reasoning": "决策理由",
  "expected_impact": "预期效果"
}}"""


def _check_needs_approval(data: dict, product: Product) -> bool:
    stype = data.get("strategy_type", "")
    changes = data.get("proposed_changes", {})
    if not isinstance(changes, dict):
        return True  # 非标准结构，需要人工审核

    if stype == "price_adjustment":
        new_price = changes.get("new_value")
        if new_price is not None:
            try:
                change_pct = abs(float(new_price) - float(product.price)) / max(float(product.price), 1)
                return change_pct > AUTO_PRICE_THRESHOLD
            except (ValueError, TypeError):
                return True  # 无法解析价格，需审核
        return False

    if stype == "promotion":
        return True  # 促销需审批

    return False  # 推荐更新自动执行


async def _execute_product_strategy(product: Product, data: dict):
    """自动执行已批准/无需审批的策略"""
    stype = data.get("strategy_type", "")
    changes = data.get("proposed_changes", {})
    if not isinstance(changes, dict):
        return

    if stype == "price_adjustment":
        new_price = changes.get("new_value")
        if new_price is not None:
            try:
                product.original_price = product.price
                product.price = float(new_price)
            except (ValueError, TypeError):
                pass

    elif stype == "recommendation_update":
        new_val = changes.get("new_value")
        if isinstance(new_val, dict):
            new_desc = new_val.get("description")
            if new_desc:
                product.description = str(new_desc)
            new_points = new_val.get("selling_points")
            if new_points:
                product.ai_selling_points = new_points
        elif isinstance(new_val, str) and new_val:
            product.description = new_val


async def execute_strategy(strategy_id: int, db: AsyncSession) -> MarketingStrategy:
    """执行已批准的策略"""
    strategy = await db.get(MarketingStrategy, strategy_id)
    if not strategy or strategy.status != StrategyStatus.approved.value:
        raise ValueError("只能执行已批准的策略")

    changes = strategy.proposed_changes

    if strategy.strategy_type == "price_adjustment":
        new_price = changes.get("new_value")
        if new_price:
            product = await db.get(Product, changes.get("product_id"))
            if product:
                product.original_price = product.price
                product.price = float(new_price)

    await db.commit()
    return strategy
