"""平台AI服务 — 负责每日顾客流量分配"""

import json
import re
from config import get_settings
from ai.providers.http_provider import HttpProvider
from constants import CATEGORY_DEMO_AFFINITY, DEMOGRAPHIC_RATIO


def get_platform_ai() -> HttpProvider:
    """获取平台AI实例（DeepSeek）"""
    settings = get_settings()
    return HttpProvider(
        api_key=settings.PLATFORM_AI_API_KEY,
        base_url=settings.PLATFORM_AI_BASE_URL,
        model_name=settings.PLATFORM_AI_MODEL,
    )


def build_allocation_prompt(merchants_data: list[dict], day: int, total_pool: int = 500) -> str:
    """构建平台AI的流量分配提示词"""
    merchants_text = ""
    for m in merchants_data:
        merchants_text += f"""
商家：{m['ai_model']}（{m['category']}）
  昨日销量：{m['yesterday_units']}件，昨日收入：¥{m['yesterday_revenue']:.0f}
  7天平均销量：{m['avg_units_7d']:.1f}件/天
  当前排名：第{m['rank']}名
  趋势：{m['trend']}
  库存：{m['stock']}件
"""

    return f"""你是保健品电商平台的「平台调度AI」。
今天是模拟第{day}天。你需要决定如何把平台的顾客流量分配给5个商家。

【5个商家昨日表现】
{merchants_text}

【平台顾客池】（按真实人口比例）
- 儿童（0-14岁）：约18%的流量
- 青年（15-35岁）：约30%的流量
- 中年（36-59岁）：约35%的流量
- 老年（60+岁）：约17%的流量

【你的分配原则】
1. 整体流量分配要体现竞争：卖得好的商家获得更多流量（正向激励）
2. 但不能让垫底商家完全没流量，要给翻身机会（底线保护）
3. 要考虑品类与人群的天然匹配度（如钙片→中老年，益生菌→青年女性）
4. 可以偶尔尝试给弱势商家分配不常见人群，看是否能打开新市场

【总流量池】今天平台共有约{total_pool}个顾客会浏览商品，请合理分配。

请严格输出以下 JSON 格式（不要输出其他任何内容）：
{{
  "allocations": [
    {{"merchant_ai": "deepseek", "demographic": "elderly", "traffic": 25}},
    {{"merchant_ai": "deepseek", "demographic": "middle", "traffic": 15}},
    ...
  ],
  "reasoning": "今天的分配策略说明"
}}

注意：
- 每个商家至少分配到1个demographic
- 所有商家的traffic总和应约为{total_pool}
- 每个demographic的总分配应接近其人口比例"""


async def allocate_customers(merchants_data: list[dict], day: int) -> dict:
    """调用平台AI进行顾客流量分配"""
    settings = get_settings()
    provider = get_platform_ai()
    prompt = build_allocation_prompt(merchants_data, day, settings.DEFAULT_TRAFFIC_POOL)

    try:
        data = await provider.generate_structured(prompt, temperature=0.5)
        if data and "allocations" in data and len(data["allocations"]) > 0:
            return data
    except Exception as e:
        print(f"⚠️ 平台AI调用异常: {e}")

    # 降级：按品类匹配度分配
    return _fallback_allocate(merchants_data, settings.DEFAULT_TRAFFIC_POOL)


def _fallback_allocate(merchants_data: list[dict], total_pool: int = 500) -> dict:
    """降级分配方案：按品类匹配度加权分配"""
    demographics = ["child", "youth", "middle", "elderly"]

    allocations = []

    for demo in demographics:
        demo_traffic = int(total_pool * DEMOGRAPHIC_RATIO[demo])

        # 计算所有商家对该人群的总亲和度
        total_affinity = 0
        for m in merchants_data:
            category = m.get("category", "")
            affinity = CATEGORY_DEMO_AFFINITY.get(category, {}).get(demo, 0.5)
            total_affinity += affinity

        # 按亲和度比例分配流量
        for m in merchants_data:
            category = m.get("category", "")
            affinity = CATEGORY_DEMO_AFFINITY.get(category, {}).get(demo, 0.5)
            traffic = max(1, int(demo_traffic * affinity / total_affinity)) if total_affinity > 0 else 1
            allocations.append({
                "merchant_ai": m["ai_model"],
                "demographic": demo,
                "traffic": traffic,
            })

    return {
        "allocations": allocations,
        "reasoning": "平台AI调用失败，使用品类匹配度加权分配降级方案",
    }
