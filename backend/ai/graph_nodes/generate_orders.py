from services.day_simulation_service import _generate_orders


async def generate_orders(state, db):
    orders_result = await _generate_orders(
        db,
        state["product_map"],
        state["traffic_allocations"],
        state["merchant_decisions"],
        state["day"],
    )

    return {
        **state,
        "orders_result": orders_result,
        "logs": [
            *state["logs"],
            {
                "node": "generate_orders",
                "merchant_count": len(orders_result),
            },
        ],
    }
