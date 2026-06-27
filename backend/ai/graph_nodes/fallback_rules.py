def build_safe_decision(merchant_info):
    return {
        "price": float(merchant_info["current_price"]),
        "promotion": "",
        "target_focus": "middle",
        "description_update": "",
        "restock": 0,
        "research_new_product": None,
        "reasoning": "fallback decision",
    }
