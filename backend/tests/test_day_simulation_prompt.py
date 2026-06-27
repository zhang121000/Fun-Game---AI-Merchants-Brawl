import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.day_simulation_service import _build_merchant_prompt


def test_build_merchant_prompt_uses_single_json_braces() -> None:
    merchant_info = {
        "category": "calcium",
        "product_name": "liquid calcium softgel",
        "current_price": 128,
        "original_price": 168,
        "stock": 200,
        "yesterday_units": 18,
        "yesterday_revenue": 2304,
        "avg_units_7d": 15.4,
        "trend": "up",
        "rank": 3,
    }

    prompt = _build_merchant_prompt(
        merchant_info,
        my_traffic=42,
        competitors=["rank 1: gpt (vitamin) trend up"],
        day=7,
    )

    assert "\n{\n  \"price\":" in prompt
    assert "\n}\n\nNotes:" in prompt
    assert "{{" not in prompt
    assert '"research_new_product": {"name": "new product name", "description": "new product description", "price": 0, "days_needed": 3} | null' in prompt
