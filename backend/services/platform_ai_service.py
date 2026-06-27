"""Platform AI service for daily customer traffic allocation."""

from config import get_settings
from ai.providers.http_provider import HttpProvider
from constants import CATEGORY_DEMO_AFFINITY, DEMOGRAPHIC_RATIO
from langsmith import traceable


def get_platform_ai() -> HttpProvider:
    """Create the platform AI provider instance."""
    settings = get_settings()
    return HttpProvider(
        api_key=settings.PLATFORM_AI_API_KEY,
        base_url=settings.PLATFORM_AI_BASE_URL,
        model_name=settings.PLATFORM_AI_MODEL,
    )


def build_allocation_prompt(
    merchants_data: list[dict],
    day: int,
    total_pool: int = 5000,
) -> str:
    """Build the structured prompt for platform traffic allocation."""
    merchants_text = ""
    for merchant in merchants_data:
        merchants_text += f"""
Merchant: {merchant['ai_model']} ({merchant['category']})
  Yesterday units: {merchant['yesterday_units']}
  Yesterday revenue: {merchant['yesterday_revenue']:.0f}
  7-day avg units: {merchant['avg_units_7d']:.1f}
  Current rank: {merchant['rank']}
  Trend: {merchant['trend']}
  Stock: {merchant['stock']}
"""

    return f"""You are the platform AI for a health products marketplace.
Today is simulation day {day}.
Allocate approximately {total_pool} customer visits across merchants.

Merchant performance:
{merchants_text}

Customer pool demographic ratios:
- child: about 18%
- youth: about 30%
- middle: about 35%
- elderly: about 17%

Allocation principles:
1. Reward stronger merchants with more traffic.
2. Keep a minimum opportunity for weaker merchants.
3. Consider natural category-demographic affinity.
4. You may occasionally explore unusual audience fits.

Return JSON only:
{{
  "allocations": [
    {{"merchant_ai": "gpt", "demographic": "youth", "traffic": 25}}
  ],
  "reasoning": "short explanation"
}}
"""


@traceable(name="platform_allocate_customers", run_type="chain")
async def allocate_customers(merchants_data: list[dict], day: int) -> dict:
    """Use the platform AI and fall back to deterministic allocation."""
    settings = get_settings()
    provider = get_platform_ai()
    prompt = build_allocation_prompt(
        merchants_data,
        day,
        settings.DEFAULT_TRAFFIC_POOL,
    )

    try:
        data = await provider.generate_structured(prompt, temperature=0.5)
        if data and data.get("allocations"):
            return data
    except Exception as exc:
        print(f"Platform AI allocation failed: {exc}")

    return _fallback_allocate(merchants_data, settings.DEFAULT_TRAFFIC_POOL)


def _fallback_allocate(merchants_data: list[dict], total_pool: int = 5000) -> dict:
    """Deterministic fallback based on category-demographic affinity."""
    demographics = ["child", "youth", "middle", "elderly"]
    allocations = []

    for demographic in demographics:
        demo_traffic = int(total_pool * DEMOGRAPHIC_RATIO[demographic])
        total_affinity = 0.0

        for merchant in merchants_data:
            category = merchant.get("category", "")
            affinity = CATEGORY_DEMO_AFFINITY.get(category, {}).get(demographic, 0.5)
            total_affinity += affinity

        for merchant in merchants_data:
            category = merchant.get("category", "")
            affinity = CATEGORY_DEMO_AFFINITY.get(category, {}).get(demographic, 0.5)
            traffic = max(1, int(demo_traffic * affinity / total_affinity)) if total_affinity > 0 else 1
            allocations.append(
                {
                    "merchant_ai": merchant["ai_model"],
                    "demographic": demographic,
                    "traffic": traffic,
                }
            )

    return {
        "allocations": allocations,
        "reasoning": "platform-ai-fallback",
    }
