from langgraph.graph import END, START, StateGraph
from langsmith import traceable

from ai.graph_nodes.allocate_traffic import (
    allocate_traffic,
    recover_allocate_traffic,
    retry_allocate_traffic,
)
from ai.graph_nodes.collect_context import collect_context
from ai.graph_nodes.finalize_day import finalize_rankings
from ai.graph_nodes.generate_orders import generate_orders
from ai.graph_nodes.merchant_decision import merchant_decision, recover_merchant_decision
from ai.graph_nodes.validate_decision import validate_decisions
from ai.graph_state import DaySimulationState


@traceable(name="graph_node_halt_day", run_type="chain")
def halt_day(state):
    return {
        **state,
        "halted": True,
        "execution_trace": [*state["execution_trace"], "halt_day"],
        "logs": [
            *state["logs"],
            {
                "node": "halt_day",
                "event": "halted",
                "halt_reason": state["halt_reason"],
            },
        ],
    }


def _route_after_collect_context(state):
    return state["next_step"]


def _route_after_allocate_traffic(state):
    return state["next_step"]


def _route_after_retry_allocate_traffic(state):
    return state["next_step"]


def _route_after_merchant_decision(state):
    return state["next_step"]


def _route_after_recover_merchant_decision(state):
    return state["next_step"]


def _route_after_validate_decision(state):
    return state["next_step"]


def _route_after_finalize(state):
    return END


def _bind_nodes(db, on_ai_complete=None):
    async def _collect_context(state):
        return await collect_context(state, db)

    async def _merchant_decision(state):
        return await merchant_decision(state, db, on_ai_complete=on_ai_complete)

    async def _generate_orders(state):
        return await generate_orders(state, db)

    return _collect_context, _merchant_decision, _generate_orders


def build_day_simulation_graph(db=None, on_ai_complete=None):
    collect_context_node, merchant_decision_node, generate_orders_node = _bind_nodes(
        db,
        on_ai_complete=on_ai_complete,
    )

    workflow = StateGraph(DaySimulationState)
    workflow.add_node("collect_context", collect_context_node)
    workflow.add_node("allocate_traffic", allocate_traffic)
    workflow.add_node("retry_allocate_traffic", retry_allocate_traffic)
    workflow.add_node("recover_allocate_traffic", recover_allocate_traffic)
    workflow.add_node("merchant_decision", merchant_decision_node)
    workflow.add_node("recover_merchant_decision", recover_merchant_decision)
    workflow.add_node("validate_decision", validate_decisions)
    workflow.add_node("generate_orders", generate_orders_node)
    workflow.add_node("finalize_day", finalize_rankings)
    workflow.add_node("halt_day", halt_day)

    workflow.add_edge(START, "collect_context")
    workflow.add_conditional_edges(
        "collect_context",
        _route_after_collect_context,
        {
            "allocate_traffic": "allocate_traffic",
            "halt_day": "halt_day",
        },
    )
    workflow.add_conditional_edges(
        "allocate_traffic",
        _route_after_allocate_traffic,
        {
            "merchant_decision": "merchant_decision",
            "retry_allocate_traffic": "retry_allocate_traffic",
            "halt_day": "halt_day",
        },
    )
    workflow.add_conditional_edges(
        "retry_allocate_traffic",
        _route_after_retry_allocate_traffic,
        {
            "retry_allocate_traffic": "retry_allocate_traffic",
            "merchant_decision": "merchant_decision",
            "recover_allocate_traffic": "recover_allocate_traffic",
            "halt_day": "halt_day",
        },
    )
    workflow.add_conditional_edges(
        "recover_allocate_traffic",
        _route_after_allocate_traffic,
        {
            "merchant_decision": "merchant_decision",
            "halt_day": "halt_day",
        },
    )
    workflow.add_conditional_edges(
        "merchant_decision",
        _route_after_merchant_decision,
        {
            "validate_decision": "validate_decision",
            "recover_merchant_decision": "recover_merchant_decision",
            "halt_day": "halt_day",
        },
    )
    workflow.add_conditional_edges(
        "recover_merchant_decision",
        _route_after_recover_merchant_decision,
        {
            "validate_decision": "validate_decision",
            "halt_day": "halt_day",
        },
    )
    workflow.add_conditional_edges(
        "validate_decision",
        _route_after_validate_decision,
        {
            "generate_orders": "generate_orders",
            "halt_day": "halt_day",
        },
    )
    workflow.add_edge("generate_orders", "finalize_day")
    workflow.add_conditional_edges(
        "finalize_day",
        _route_after_finalize,
        {
            END: END,
        },
    )
    workflow.add_edge("halt_day", END)

    return workflow.compile()


@traceable(name="day_simulation_graph", run_type="chain")
async def run_day_simulation_graph(state, db, on_ai_complete=None):
    graph = build_day_simulation_graph(db, on_ai_complete=on_ai_complete)
    return await graph.ainvoke(state)
