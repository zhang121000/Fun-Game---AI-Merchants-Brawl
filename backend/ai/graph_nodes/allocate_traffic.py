import asyncio

from langsmith import traceable

from config import get_settings
from services.platform_ai_service import allocate_customers, _fallback_allocate


def apply_allocation_result(
    state,
    allocation_result,
    *,
    trace_node="allocate_traffic",
    log_node="allocate_traffic",
):
    execution_trace = [*state.get("execution_trace", []), trace_node]
    return {
        **state,
        "traffic_allocations": allocation_result.get("allocations", []),
        "platform_reasoning": allocation_result.get("reasoning", ""),
        "next_step": "merchant_decision",
        "execution_trace": execution_trace,
        "node_status": {
            **state.get("node_status", {}),
            "allocate_traffic": "success",
        },
        "logs": [
            *state["logs"],
            {
                "node": log_node,
                "allocation_count": len(allocation_result.get("allocations", [])),
                "reasoning": allocation_result.get("reasoning", ""),
            },
        ],
    }


@traceable(name="graph_node_allocate_traffic", run_type="chain")
async def allocate_traffic(state):
    attempt = state.get("retry_counts", {}).get("allocate_traffic", 0) + 1

    try:
        allocation_result = await asyncio.wait_for(
            allocate_customers(state["merchants_data"], state["day"]),
            timeout=15.0,
        )
    except Exception as exc:
        retry_counts = {
            **state.get("retry_counts", {}),
            "allocate_traffic": attempt,
        }
        node_status = {
            **state.get("node_status", {}),
            "allocate_traffic": "retry_needed",
        }

        return {
            **state,
            "next_step": "retry_allocate_traffic",
            "retry_counts": retry_counts,
            "node_status": node_status,
            "errors": [
                *state.get("errors", []),
                {
                    "node": "allocate_traffic",
                    "event": "attempt_failed",
                    "attempt": attempt,
                    "scope": "platform",
                    "recoverable": True,
                    "error": str(exc),
                },
            ],
        }

    return apply_allocation_result(state, allocation_result)


@traceable(name="graph_node_retry_allocate_traffic", run_type="chain")
async def retry_allocate_traffic(state):
    retry_count = state.get("retry_counts", {}).get("allocate_traffic", 0)
    retried_state = {
        **state,
        "execution_trace": [*state.get("execution_trace", []), "retry_allocate_traffic"],
        "logs": [
            *state.get("logs", []),
            {
                "node": "retry_allocate_traffic",
                "retry_count": retry_count,
            },
        ],
    }
    if retry_count < 2:
        return await allocate_traffic(retried_state)

    return {
        **retried_state,
        "next_step": "recover_allocate_traffic",
    }


@traceable(name="graph_node_recover_allocate_traffic", run_type="chain")
def recover_allocate_traffic(state):
    settings = get_settings()
    allocation_result = _fallback_allocate(
        state["merchants_data"],
        settings.DEFAULT_TRAFFIC_POOL,
    )
    attempts = state.get("retry_counts", {}).get("allocate_traffic", 0)

    if allocation_result.get("allocations"):
        updated = apply_allocation_result(
            state,
            allocation_result,
            trace_node="recover_allocate_traffic",
            log_node="recover_allocate_traffic",
        )
        return {
            **updated,
            "node_status": {
                **updated.get("node_status", {}),
                "allocate_traffic": "fallback",
            },
            "recovered_error_count": state.get("recovered_error_count", 0) + 1,
            "retry_summary": {
                **state.get("retry_summary", {}),
                "allocate_traffic": {
                    "attempts": attempts,
                    "status": "fallback",
                    "used_fallback": True,
                },
            },
            "logs": [
                *updated.get("logs", []),
                {
                    "node": "recover_allocate_traffic",
                    "event": "fallback_recovery",
                    "attempts": attempts,
                    "used_fallback": True,
                    "allocation_count": len(allocation_result.get("allocations", [])),
                    "reasoning": allocation_result.get("reasoning", ""),
                },
            ],
        }

    return {
        **state,
        "traffic_allocations": [],
        "platform_reasoning": allocation_result.get("reasoning", ""),
        "node_status": {
            **state.get("node_status", {}),
            "allocate_traffic": "failed",
        },
        "retry_summary": {
            **state.get("retry_summary", {}),
            "allocate_traffic": {
                "attempts": attempts,
                "status": "failed",
                "used_fallback": False,
            },
        },
        "halt_reason": "platform_allocation_failed",
        "next_step": "halt_day",
        "execution_trace": [*state.get("execution_trace", []), "recover_allocate_traffic"],
        "logs": [
            *state.get("logs", []),
            {
                "node": "recover_allocate_traffic",
                "event": "fallback_exhausted",
                "attempts": attempts,
                "used_fallback": False,
                "allocation_count": 0,
                "reasoning": allocation_result.get("reasoning", ""),
            },
        ],
    }
