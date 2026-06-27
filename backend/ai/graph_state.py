from typing import Any, TypedDict


class DaySimulationState(TypedDict):
    day: int
    merchants_data: list[dict[str, Any]]
    product_map: dict[str, Any]
    traffic_allocations: list[dict[str, Any]]
    merchant_decisions: dict[str, dict[str, Any]]
    validation_results: dict[str, dict[str, Any]]
    orders_result: list[dict[str, Any]]
    rankings: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]
    platform_reasoning: str
    logs: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    execution_path: str
    next_step: str
    halt_reason: str | None
    graph_version: str
    execution_trace: list[str]
    node_status: dict[str, str]
    retry_counts: dict[str, int]
    retry_summary: dict[str, Any]
    recovered_error_count: int
    halted: bool
    failed_merchants: list[str]
    merchant_status: dict[str, dict[str, Any]]


def build_initial_day_state(day: int) -> DaySimulationState:
    return {
        "day": day,
        "merchants_data": [],
        "product_map": {},
        "traffic_allocations": [],
        "merchant_decisions": {},
        "validation_results": {},
        "orders_result": [],
        "rankings": [],
        "suggestions": [],
        "platform_reasoning": "",
        "logs": [],
        "errors": [],
        "execution_path": "langgraph",
        "next_step": "collect_context",
        "halt_reason": None,
        "graph_version": "phase3",
        "execution_trace": [],
        "node_status": {
            "collect_context": "pending",
            "allocate_traffic": "pending",
            "merchant_decision": "pending",
            "validate_decision": "pending",
            "generate_orders": "pending",
            "finalize_day": "pending",
        },
        "retry_counts": {},
        "retry_summary": {},
        "recovered_error_count": 0,
        "halted": False,
        "failed_merchants": [],
        "merchant_status": {},
    }
