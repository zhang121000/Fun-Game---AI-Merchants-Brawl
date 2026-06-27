from ai.graph_nodes.fallback_rules import build_safe_decision
from langsmith import traceable
from services.day_simulation_service import _get_all_decisions


_MAX_MERCHANT_ATTEMPTS = 2


def _build_merchant_status(status, attempts, recoverable):
    return {
        "status": status,
        "attempts": attempts,
        "recoverable": recoverable,
    }


@traceable(name="graph_node_merchant_decision", run_type="chain")
async def merchant_decision(state, db, on_ai_complete=None):
    decisions = {**state.get("merchant_decisions", {})}
    merchant_status = {**state.get("merchant_status", {})}
    failed_merchants = []
    errors = [*state.get("errors", [])]
    execution_trace = [*state.get("execution_trace", []), "merchant_decision"]
    merchants_data = state.get("merchants_data", [])
    for merchant_info in merchants_data:
        ai_model = merchant_info["ai_model"]
        decision_payload = {}
        attempts = 0

        while attempts < _MAX_MERCHANT_ATTEMPTS:
            attempts += 1
            result = await _get_all_decisions(
                db,
                state["product_map"],
                [merchant_info],
                state["traffic_allocations"],
                state["day"],
                on_ai_complete=None,
            )
            decision_payload = result.get(ai_model, {})
            if decision_payload:
                decisions[ai_model] = decision_payload
                merchant_status[ai_model] = _build_merchant_status(
                    "success" if attempts == 1 else "retried_success",
                    attempts,
                    False,
                )
                break

        if not decision_payload:
            failed_merchants.append(ai_model)
            merchant_status[ai_model] = _build_merchant_status("failed", attempts, True)

        if on_ai_complete:
            on_ai_complete(ai_model)

    decision_count = sum(
        1 for merchant_info in merchants_data if decisions.get(merchant_info["ai_model"])
    )

    if failed_merchants:
        errors.append(
            {
                "node": "merchant_decision",
                "error": "missing_decisions",
                "expected": len(merchants_data),
                "actual": decision_count,
                "failed_merchants": failed_merchants,
            }
        )

    if decision_count == 0:
        next_step = "halt_day"
        halt_reason = "merchant_decision_failed"
    elif failed_merchants:
        next_step = "recover_merchant_decision"
        halt_reason = state.get("halt_reason")
    else:
        next_step = "validate_decision"
        halt_reason = state.get("halt_reason")

    return {
        **state,
        "merchant_decisions": decisions,
        "merchant_status": merchant_status,
        "failed_merchants": failed_merchants,
        "errors": errors,
        "next_step": next_step,
        "halt_reason": halt_reason,
        "execution_trace": execution_trace,
        "logs": [
            *state["logs"],
            {
                "node": "merchant_decision",
                "decision_count": decision_count,
                "failed_count": len(failed_merchants),
            },
        ],
    }


@traceable(name="graph_node_recover_merchant_decision", run_type="chain")
async def recover_merchant_decision(state):
    merchant_lookup = {
        merchant_info["ai_model"]: merchant_info
        for merchant_info in state.get("merchants_data", [])
    }
    decisions = {**state.get("merchant_decisions", {})}
    merchant_status = {**state.get("merchant_status", {})}
    recovered_error_count = state.get("recovered_error_count", 0)
    logs = [*state.get("logs", [])]

    for ai_model in state.get("failed_merchants", []):
        merchant_info = merchant_lookup.get(ai_model)
        if not merchant_info:
            continue

        decisions[ai_model] = build_safe_decision(merchant_info)
        merchant_status[ai_model] = {
            **merchant_status.get(ai_model, {}),
            "status": "fallback",
            "recoverable": False,
        }
        recovered_error_count += 1
        logs.append(
            {
                "node": "merchant_decision",
                "event": "fallback_applied",
                "scope": "merchant",
                "ai_model": ai_model,
            }
        )

    return {
        **state,
        "merchant_decisions": decisions,
        "merchant_status": merchant_status,
        "recovered_error_count": recovered_error_count,
        "next_step": "validate_decision",
        "execution_trace": [*state.get("execution_trace", []), "recover_merchant_decision"],
        "logs": logs,
    }
