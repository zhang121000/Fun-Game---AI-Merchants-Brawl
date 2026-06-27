from sqlalchemy import select
from langsmith import traceable

from models.merchant import Merchant
from models.product import Product
from services.day_simulation_service import _collect_merchant_performance


@traceable(name="graph_node_collect_context", run_type="chain")
async def collect_context(state, db):
    products = (
        await db.execute(select(Product).where(Product.is_active == True))
    ).scalars().all()
    merchants = (await db.execute(select(Merchant))).scalars().all()

    product_map = {product.ai_model: product for product in products}
    merchants_data = await _collect_merchant_performance(
        db, merchants, product_map, state["day"] - 1
    )

    return {
        **state,
        "product_map": product_map,
        "merchants_data": merchants_data,
        "next_step": "allocate_traffic",
        "execution_trace": [*state.get("execution_trace", []), "collect_context"],
        "node_status": {
            **state.get("node_status", {}),
            "collect_context": "success",
        },
        "logs": [
            *state["logs"],
            {
                "node": "collect_context",
                "merchant_count": len(merchants_data),
                "product_count": len(product_map),
            },
        ],
    }
