"""营销策略生成的提示词构建器"""

from ai.prompts.persona_templates import get_persona_prompt


def build_strategy_prompt(
    model_key: str,
    sales_summary: dict,
    stock_summary: list[dict],
    competitor_prices: dict,
) -> str:
    persona = get_persona_prompt(model_key)

    return f"""{persona}

【当前经营数据】
- 最近7天订单量：{sales_summary.get('orders_7d', 0)}
- 最近7天总销售额：¥{sales_summary.get('revenue_7d', 0):.0f}
- 平均客单价：¥{sales_summary.get('avg_order_value', 0):.0f}
- 人群购买分布：{sales_summary.get('demographic_breakdown', {})}

【库存状况】
{stock_summary}

【竞争对手价格范围】
{competitor_prices}

请根据你的经营风格和以上数据，生成一条营销策略调整建议。
可选策略类型：price_adjustment（调价）、promotion（促销活动）、bundle（捆绑销售）、recommendation_update（更新推荐语）

请严格输出以下 JSON 格式（不要输出其他任何内容）：
{{
  "strategy_type": "price_adjustment|promotion|bundle|recommendation_update",
  "title": "策略标题（简短，15字以内）",
  "description": "详细说明这个策略的内容",
  "proposed_changes": {{
    "target_product_ids": [商品ID列表],
    "old_values": {{"字段名": "旧值"}},
    "new_values": {{"字段名": "新值"}}
  }},
  "reasoning": "你做出这个决策的理由",
  "expected_impact": "预期效果"
}}"""
