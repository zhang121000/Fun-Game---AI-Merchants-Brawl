from ai.graph_nodes.fallback_rules import build_safe_decision
from langsmith import traceable


def validate_single_decision(ai_model, merchant_info, decision):
    issues = []
    safe = build_safe_decision(merchant_info)
    candidate = {**safe, **(decision or {})}

    current_price = float(merchant_info["current_price"])
    min_price = round(current_price * 0.85, 2)
    max_price = round(current_price * 1.15, 2)

    if candidate["price"] < min_price or candidate["price"] > max_price:
        issues.append("price_out_of_range")
        candidate["price"] = max(min(candidate["price"], max_price), min_price)

    if candidate["restock"] and candidate["restock"] < 0:
        issues.append("invalid_restock")
        candidate["restock"] = 0

    return {
        "ai_model": ai_model,
        "validated_decision": candidate,
        "used_fallback": bool(issues),
        "issues": issues,
    }


@traceable(name="graph_node_validate_decision", run_type="chain")
def validate_decisions(state):
    validated = {}
    fallback_models = {
        ai_model
        for ai_model, status in state.get("merchant_status", {}).items()
        if status.get("status") == "fallback"
    }
    for merchant_info in state["merchants_data"]:
        ai_model = merchant_info["ai_model"]
        validated[ai_model] = validate_single_decision(
            ai_model,
            merchant_info,
            state["merchant_decisions"].get(ai_model, {}),
        )
        if validated[ai_model]["used_fallback"]:
            fallback_models.add(ai_model)

    fallback_count = len(fallback_models)
    errors = [*state.get("errors", [])]
    execution_trace = [*state.get("execution_trace", []), "validate_decision"]
    executable_count = sum(
        1 for result in validated.values() if result.get("validated_decision")
    )
    failed_merchants = [*state.get("failed_merchants", [])]
    if fallback_count == len(validated) and validated:
        errors.append(
            {
                "node": "validate_decision",
                "error": "all_decisions_used_fallback",
                "fallback_count": fallback_count,
            }
        )

    if executable_count == 0:
        next_step = "halt_day"
        halt_reason = "no_executable_decisions"
        validation_route = "halt_day"
    elif fallback_count == len(validated) and validated:
        next_step = "generate_orders"
        halt_reason = state.get("halt_reason")
        validation_route = "all_fallback"
    elif failed_merchants or fallback_count > 0:
        next_step = "generate_orders"
        halt_reason = state.get("halt_reason")
        validation_route = "partial_failed"
    else:
        next_step = "generate_orders"
        halt_reason = state.get("halt_reason")
        validation_route = "all_valid"

    return {
        **state,
        "validation_results": validated,
        "merchant_decisions": {
            ai_model: result["validated_decision"]
            for ai_model, result in validated.items()
        },
        "errors": errors,
        "retry_summary": {
            **state.get("retry_summary", {}),
            "merchant_decision": {
                "failed_merchants": failed_merchants,
                "fallback_count": fallback_count,
            },
        },
        "next_step": next_step,
        "halt_reason": halt_reason,
        "execution_trace": execution_trace,
        "logs": [
            *state["logs"],
            {
                "node": "validate_decision",
                "fallback_count": fallback_count,
                "route": validation_route,
            },
        ],
    }
