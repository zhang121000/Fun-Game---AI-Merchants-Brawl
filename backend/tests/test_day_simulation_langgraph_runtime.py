import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.graph_state import build_initial_day_state
from ai.graphs.day_simulation_graph import build_day_simulation_graph, run_day_simulation_graph


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_build_day_simulation_graph_returns_compiled_graph():
    graph = build_day_simulation_graph()
    assert hasattr(graph, "ainvoke")


@pytest.mark.anyio
async def test_run_day_simulation_graph_uses_compiled_graph(monkeypatch):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object()},
            "merchants_data": [
                {
                    "ai_model": "gpt",
                    "current_price": 100.0,
                    "original_price": 120.0,
                    "stock": 20,
                    "rank": 1,
                }
            ],
            "next_step": "allocate_traffic",
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_traffic(state):
        return {
            **state,
            "traffic_allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 10}],
            "next_step": "merchant_decision",
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    async def fake_merchant_decision(state, db, on_ai_complete=None):
        return {
            **state,
            "merchant_decisions": {
                "gpt": {
                    "price": 100.0,
                    "promotion": "",
                    "target_focus": "youth",
                    "description_update": "",
                    "restock": 0,
                    "research_new_product": None,
                    "reasoning": "ok",
                }
            },
            "next_step": "validate_decision",
            "execution_trace": [*state["execution_trace"], "merchant_decision"],
            "logs": [*state["logs"], {"node": "merchant_decision"}],
        }

    def fake_validate_decisions(state):
        return {
            **state,
            "validation_results": {
                "gpt": {
                    "validated_decision": state["merchant_decisions"]["gpt"],
                    "used_fallback": False,
                    "issues": [],
                }
            },
            "next_step": "generate_orders",
            "execution_trace": [*state["execution_trace"], "validate_decision"],
            "logs": [*state["logs"], {"node": "validate_decision"}],
        }

    async def fake_generate_orders(state, db):
        return {
            **state,
            "orders_result": [
                {
                    "merchant_ai": "gpt",
                    "category": "vitamin",
                    "product_name": "demo",
                    "traffic_received": 10,
                    "units_sold": 4,
                    "revenue": 400.0,
                    "rank": 0,
                }
            ],
            "next_step": "finalize_day",
            "execution_trace": [*state["execution_trace"], "generate_orders"],
            "logs": [*state["logs"], {"node": "generate_orders"}],
        }

    def fake_finalize_rankings(state):
        return {
            **state,
            "rankings": [
                {
                    "merchant_ai": "gpt",
                    "category": "vitamin",
                    "product_name": "demo",
                    "traffic_received": 10,
                    "units_sold": 4,
                    "revenue": 400.0,
                    "rank": 1,
                }
            ],
            "halt_reason": "completed",
            "execution_trace": [*state["execution_trace"], "finalize_day"],
            "logs": [*state["logs"], {"node": "finalize_day"}],
        }

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.merchant_decision", fake_merchant_decision)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.validate_decisions", fake_validate_decisions)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.generate_orders", fake_generate_orders)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.finalize_rankings", fake_finalize_rankings)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert state["halt_reason"] == "completed"
    assert state["execution_trace"] == [
        "collect_context",
        "allocate_traffic",
        "merchant_decision",
        "validate_decision",
        "generate_orders",
        "finalize_day",
    ]


@pytest.mark.anyio
async def test_run_day_simulation_graph_keeps_running_when_all_decisions_fallback(monkeypatch):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object()},
            "merchants_data": [
                {
                    "ai_model": "gpt",
                    "current_price": 100.0,
                    "original_price": 120.0,
                    "stock": 20,
                    "rank": 1,
                }
            ],
            "next_step": "allocate_traffic",
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_traffic(state):
        return {
            **state,
            "traffic_allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 10}],
            "next_step": "merchant_decision",
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    async def fake_merchant_decision(state, db, on_ai_complete=None):
        return {
            **state,
            "merchant_decisions": {"gpt": {}},
            "next_step": "validate_decision",
            "execution_trace": [*state["execution_trace"], "merchant_decision"],
            "logs": [*state["logs"], {"node": "merchant_decision"}],
        }

    def fake_validate_decisions(state):
        return {
            **state,
            "merchant_decisions": {
                "gpt": {
                    "price": 100.0,
                    "promotion": "",
                    "target_focus": "middle",
                    "description_update": "",
                    "restock": 0,
                    "research_new_product": None,
                    "reasoning": "fallback decision",
                }
            },
            "validation_results": {
                "gpt": {
                    "validated_decision": {
                        "price": 100.0,
                        "promotion": "",
                        "target_focus": "middle",
                        "description_update": "",
                        "restock": 0,
                        "research_new_product": None,
                        "reasoning": "fallback decision",
                    },
                    "used_fallback": True,
                    "issues": ["missing_fields"],
                }
            },
            "errors": [
                *state["errors"],
                {
                    "node": "validate_decision",
                    "error": "all_decisions_used_fallback",
                    "fallback_count": 1,
                },
            ],
            "next_step": "generate_orders",
            "execution_trace": [*state["execution_trace"], "validate_decision"],
            "logs": [*state["logs"], {"node": "validate_decision", "fallback_count": 1}],
        }

    async def fake_generate_orders(state, db):
        return {
            **state,
            "orders_result": [
                {
                    "merchant_ai": "gpt",
                    "category": "vitamin",
                    "product_name": "demo",
                    "traffic_received": 10,
                    "units_sold": 1,
                    "revenue": 100.0,
                    "rank": 0,
                }
            ],
            "next_step": "finalize_day",
            "execution_trace": [*state["execution_trace"], "generate_orders"],
            "logs": [*state["logs"], {"node": "generate_orders"}],
        }

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.merchant_decision", fake_merchant_decision)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.validate_decisions", fake_validate_decisions)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.generate_orders", fake_generate_orders)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert state["halt_reason"] == "completed"
    assert state["errors"][-1]["error"] == "all_decisions_used_fallback"
    assert state["rankings"][0]["units_sold"] == 1


@pytest.mark.anyio
async def test_run_day_simulation_graph_halts_on_platform_failure(monkeypatch):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object()},
            "merchants_data": [{"ai_model": "gpt"}],
            "next_step": "allocate_traffic",
            "node_status": {**state["node_status"], "collect_context": "success"},
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_traffic(state):
        return {
            **state,
            "next_step": "halt_day",
            "halt_reason": "platform_allocation_failed",
            "node_status": {**state["node_status"], "allocate_traffic": "failed"},
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert state["halted"] is True
    assert state["halt_reason"] == "platform_allocation_failed"
    assert state["execution_trace"][-1] == "halt_day"


@pytest.mark.anyio
async def test_run_day_simulation_graph_halts_after_platform_retry_and_recovery_exhaustion(
    monkeypatch,
):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object()},
            "merchants_data": [{"ai_model": "gpt"}],
            "next_step": "allocate_traffic",
            "node_status": {**state["node_status"], "collect_context": "success"},
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_customers(merchants_data, day):
        del merchants_data, day
        raise TimeoutError("platform timeout")

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graph_nodes.allocate_traffic.allocate_customers", fake_allocate_customers)
    monkeypatch.setattr(
        "ai.graph_nodes.allocate_traffic._fallback_allocate",
        lambda merchants_data, traffic_pool: {
            "allocations": [],
            "reasoning": "platform-ai-fallback",
        },
    )

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert state["halted"] is True
    assert state["halt_reason"] == "platform_allocation_failed"
    assert state["execution_trace"] == [
        "collect_context",
        "retry_allocate_traffic",
        "retry_allocate_traffic",
        "recover_allocate_traffic",
        "halt_day",
    ]
    assert len(state["errors"]) == 2
    assert [error["attempt"] for error in state["errors"]] == [1, 2]
    assert state["retry_summary"]["allocate_traffic"] == {
        "attempts": 2,
        "status": "failed",
        "used_fallback": False,
    }
    assert [log["node"] for log in state["logs"][-3:]] == [
        "retry_allocate_traffic",
        "recover_allocate_traffic",
        "halt_day",
    ]


@pytest.mark.anyio
async def test_run_day_simulation_graph_routes_failed_merchants_through_recovery(monkeypatch):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object(), "qwen": object()},
            "merchants_data": [{"ai_model": "gpt"}, {"ai_model": "qwen"}],
            "next_step": "allocate_traffic",
            "node_status": {**state["node_status"], "collect_context": "success"},
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_traffic(state):
        return {
            **state,
            "traffic_allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 10}],
            "next_step": "merchant_decision",
            "node_status": {**state["node_status"], "allocate_traffic": "success"},
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    async def fake_merchant_decision(state, db, on_ai_complete=None):
        return {
            **state,
            "merchant_decisions": {
                "gpt": {
                    "price": 100.0,
                    "promotion": "",
                    "target_focus": "youth",
                    "description_update": "",
                    "restock": 0,
                    "research_new_product": None,
                    "reasoning": "ok",
                }
            },
            "merchant_status": {"gpt": {"status": "success"}, "qwen": {"status": "failed", "attempts": 2}},
            "failed_merchants": ["qwen"],
            "next_step": "recover_merchant_decision",
            "execution_trace": [*state["execution_trace"], "merchant_decision"],
            "logs": [*state["logs"], {"node": "merchant_decision"}],
        }

    async def fake_recover_merchant_decision(state):
        return {
            **state,
            "merchant_decisions": {
                **state["merchant_decisions"],
                "qwen": {
                    "price": 80.0,
                    "promotion": "",
                    "target_focus": "middle",
                    "description_update": "",
                    "restock": 0,
                    "research_new_product": None,
                    "reasoning": "fallback decision",
                },
            },
            "merchant_status": {
                **state["merchant_status"],
                "qwen": {"status": "fallback", "attempts": 2},
            },
            "recovered_error_count": 1,
            "next_step": "validate_decision",
            "execution_trace": [*state["execution_trace"], "recover_merchant_decision"],
            "logs": [*state["logs"], {"node": "recover_merchant_decision"}],
        }

    def fake_validate_decisions(state):
        return {
            **state,
            "validation_results": {
                ai_model: {
                    "validated_decision": decision,
                    "used_fallback": ai_model == "qwen",
                    "issues": [],
                }
                for ai_model, decision in state["merchant_decisions"].items()
            },
            "next_step": "generate_orders",
            "execution_trace": [*state["execution_trace"], "validate_decision"],
            "logs": [*state["logs"], {"node": "validate_decision"}],
        }

    async def fake_generate_orders(state, db):
        return {
            **state,
            "orders_result": [
                {
                    "merchant_ai": "gpt",
                    "category": "vitamin",
                    "product_name": "demo",
                    "traffic_received": 10,
                    "units_sold": 4,
                    "revenue": 400.0,
                    "rank": 0,
                }
            ],
            "next_step": "finalize_day",
            "execution_trace": [*state["execution_trace"], "generate_orders"],
            "logs": [*state["logs"], {"node": "generate_orders"}],
        }

    def fake_finalize_rankings(state):
        return {
            **state,
            "rankings": [*state["orders_result"]],
            "halt_reason": "completed",
            "execution_trace": [*state["execution_trace"], "finalize_day"],
            "logs": [*state["logs"], {"node": "finalize_day"}],
        }

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.merchant_decision", fake_merchant_decision)
    monkeypatch.setattr(
        "ai.graphs.day_simulation_graph.recover_merchant_decision",
        fake_recover_merchant_decision,
    )
    monkeypatch.setattr("ai.graphs.day_simulation_graph.validate_decisions", fake_validate_decisions)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.generate_orders", fake_generate_orders)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.finalize_rankings", fake_finalize_rankings)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert "recover_merchant_decision" in state["execution_trace"]


@pytest.mark.anyio
async def test_run_day_simulation_graph_halts_when_all_merchant_decisions_fail(monkeypatch):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object()},
            "merchants_data": [{"ai_model": "gpt"}],
            "next_step": "allocate_traffic",
            "node_status": {**state["node_status"], "collect_context": "success"},
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_traffic(state):
        return {
            **state,
            "traffic_allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 10}],
            "next_step": "merchant_decision",
            "node_status": {**state["node_status"], "allocate_traffic": "success"},
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    async def fake_get_all_decisions(
        db,
        product_map,
        merchants_data,
        allocations,
        day,
        on_ai_complete=None,
    ):
        del db, product_map, merchants_data, allocations, day, on_ai_complete
        return {}

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)
    monkeypatch.setattr("ai.graph_nodes.merchant_decision._get_all_decisions", fake_get_all_decisions)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert state["halted"] is True
    assert state["halt_reason"] == "merchant_decision_failed"
    assert state["failed_merchants"] == ["gpt"]
    assert state["execution_trace"][-2:] == ["merchant_decision", "halt_day"]


@pytest.mark.anyio
async def test_run_day_simulation_graph_honors_halt_route_from_merchant_recovery(monkeypatch):
    async def fake_collect_context(state, db):
        return {
            **state,
            "product_map": {"gpt": object()},
            "merchants_data": [{"ai_model": "gpt"}],
            "next_step": "allocate_traffic",
            "node_status": {**state["node_status"], "collect_context": "success"},
            "execution_trace": [*state["execution_trace"], "collect_context"],
            "logs": [*state["logs"], {"node": "collect_context"}],
        }

    async def fake_allocate_traffic(state):
        return {
            **state,
            "traffic_allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 10}],
            "next_step": "merchant_decision",
            "node_status": {**state["node_status"], "allocate_traffic": "success"},
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    async def fake_merchant_decision(state, db, on_ai_complete=None):
        del db, on_ai_complete
        return {
            **state,
            "failed_merchants": ["gpt"],
            "next_step": "recover_merchant_decision",
            "execution_trace": [*state["execution_trace"], "merchant_decision"],
            "logs": [*state["logs"], {"node": "merchant_decision"}],
        }

    async def fake_recover_merchant_decision(state):
        return {
            **state,
            "halt_reason": "merchant_recovery_aborted",
            "next_step": "halt_day",
            "execution_trace": [*state["execution_trace"], "recover_merchant_decision"],
            "logs": [*state["logs"], {"node": "recover_merchant_decision"}],
        }

    def fail_validate_decisions(state):
        raise AssertionError(f"validate_decision should not run: {state['execution_trace']}")

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.merchant_decision", fake_merchant_decision)
    monkeypatch.setattr(
        "ai.graphs.day_simulation_graph.recover_merchant_decision",
        fake_recover_merchant_decision,
    )
    monkeypatch.setattr("ai.graphs.day_simulation_graph.validate_decisions", fail_validate_decisions)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert state["halted"] is True
    assert state["halt_reason"] == "merchant_recovery_aborted"
    assert state["execution_trace"][-2:] == ["recover_merchant_decision", "halt_day"]
