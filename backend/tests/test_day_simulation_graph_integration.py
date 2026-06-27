import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.graph_state import build_initial_day_state
from ai.graphs.day_simulation_graph import run_day_simulation_graph
from services.day_simulation_service import _build_advance_day_response


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_build_advance_day_response_includes_execution_path() -> None:
    graph_state = {
        "day": 4,
        "rankings": [{"merchant_ai": "gpt", "units_sold": 3, "revenue": 300.0}],
        "platform_reasoning": "graph reasoning",
        "suggestions": [{"type": "warning"}],
        "execution_path": "langgraph",
        "graph_version": "phase3",
        "halt_reason": "completed",
        "errors": [],
        "execution_trace": [],
    }

    result = _build_advance_day_response(graph_state)

    assert result["day"] == 4
    assert result["execution_path"] == "langgraph"
    assert result["total_orders"] == 3


def test_build_advance_day_response_includes_graph_metadata() -> None:
    graph_state = {
        "day": 4,
        "rankings": [{"merchant_ai": "gpt", "units_sold": 3, "revenue": 300.0}],
        "platform_reasoning": "graph reasoning",
        "suggestions": [{"type": "warning"}],
        "execution_path": "langgraph",
        "graph_version": "phase3",
        "halt_reason": "completed",
        "errors": [{"node": "allocate_traffic", "error": "timeout"}],
        "execution_trace": ["collect_context", "allocate_traffic"],
    }

    result = _build_advance_day_response(graph_state)

    assert result["execution_path"] == "langgraph"
    assert result["graph_version"] == "phase3"
    assert result["halt_reason"] == "completed"
    assert result["error_count"] == 1
    assert result["execution_trace"] == ["collect_context", "allocate_traffic"]


def test_build_advance_day_response_includes_phase3_recovery_metadata() -> None:
    graph_state = {
        "day": 6,
        "rankings": [],
        "platform_reasoning": "platform-ai-fallback",
        "suggestions": [],
        "execution_path": "langgraph",
        "graph_version": "phase3",
        "halt_reason": "platform_allocation_failed",
        "errors": [{"node": "allocate_traffic", "error": "timeout"}],
        "execution_trace": ["collect_context", "allocate_traffic", "halt_day"],
        "halted": True,
        "recovered_error_count": 1,
        "failed_merchants": ["qwen"],
        "retry_summary": {"allocate_traffic": {"attempts": 2, "used_fallback": True}},
    }

    result = _build_advance_day_response(graph_state)

    assert result["halted"] is True
    assert result["recovered_error_count"] == 1
    assert result["failed_merchants"] == ["qwen"]
    assert result["retry_summary"]["allocate_traffic"]["used_fallback"] is True


def test_build_advance_day_response_preserves_existing_totals_for_halted_run() -> None:
    graph_state = {
        "day": 6,
        "rankings": [],
        "platform_reasoning": "",
        "suggestions": [],
        "execution_path": "langgraph",
        "graph_version": "phase3",
        "halt_reason": "platform_allocation_failed",
        "errors": [],
        "execution_trace": ["halt_day"],
        "halted": True,
        "recovered_error_count": 0,
        "failed_merchants": [],
        "retry_summary": {},
    }

    result = _build_advance_day_response(graph_state)

    assert result["total_orders"] == 0
    assert result["total_revenue"] == 0


@pytest.mark.anyio
async def test_run_day_simulation_graph_returns_rankings(monkeypatch):
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
                }
            ],
            "logs": [*state["logs"], {"node": "generate_orders"}],
        }

    monkeypatch.setattr("ai.graphs.day_simulation_graph.collect_context", fake_collect_context)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.allocate_traffic", fake_allocate_traffic)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.merchant_decision", fake_merchant_decision)
    monkeypatch.setattr("ai.graphs.day_simulation_graph.generate_orders", fake_generate_orders)

    state = await run_day_simulation_graph(build_initial_day_state(1), db=None)

    assert "rankings" in state
    assert state["logs"][0]["node"] == "collect_context"
