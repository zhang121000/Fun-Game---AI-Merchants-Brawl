import sys
from pathlib import Path

import pytest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.graph_nodes.allocate_traffic import (
    apply_allocation_result,
    allocate_traffic,
    recover_allocate_traffic,
    retry_allocate_traffic,
)
from ai.graph_nodes.collect_context import collect_context
from ai.graph_nodes.finalize_day import finalize_rankings
from ai.graphs.day_simulation_graph import halt_day
from ai.graph_nodes.merchant_decision import merchant_decision, recover_merchant_decision
from ai.graph_nodes.validate_decision import validate_decisions, validate_single_decision


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_apply_allocation_result_updates_reasoning_and_allocations() -> None:
    state = {
        "traffic_allocations": [],
        "platform_reasoning": "",
        "logs": [],
        "errors": [],
    }
    allocation_result = {
        "allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 12}],
        "reasoning": "fallback allocation",
    }

    updated = apply_allocation_result(state, allocation_result)

    assert updated["traffic_allocations"] == allocation_result["allocations"]
    assert updated["platform_reasoning"] == "fallback allocation"
    assert updated["logs"][-1]["node"] == "allocate_traffic"


def test_apply_allocation_result_advances_graph_trace() -> None:
    state = {
        "traffic_allocations": [],
        "platform_reasoning": "",
        "logs": [],
        "errors": [],
        "execution_trace": [],
        "next_step": "allocate_traffic",
    }
    allocation_result = {
        "allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 12}],
        "reasoning": "fallback allocation",
    }

    updated = apply_allocation_result(state, allocation_result)

    assert updated["execution_trace"][-1] == "allocate_traffic"
    assert updated["next_step"] == "merchant_decision"


def test_graph_nodes_expose_traceable_wrappers() -> None:
    traced_nodes = [
        collect_context,
        allocate_traffic,
        retry_allocate_traffic,
        recover_allocate_traffic,
        merchant_decision,
        recover_merchant_decision,
        validate_decisions,
        finalize_rankings,
        halt_day,
    ]

    assert all(hasattr(node, "__wrapped__") for node in traced_nodes)


@pytest.mark.anyio
async def test_allocate_traffic_marks_retry_needed_on_first_failure(monkeypatch) -> None:
    from ai.graph_nodes.allocate_traffic import allocate_traffic

    async def fake_allocate_customers(merchants_data, day):
        raise TimeoutError("platform timeout")

    monkeypatch.setattr("ai.graph_nodes.allocate_traffic.allocate_customers", fake_allocate_customers)

    state = {
        "day": 2,
        "merchants_data": [{"ai_model": "gpt"}],
        "traffic_allocations": [],
        "platform_reasoning": "",
        "logs": [],
        "errors": [],
        "execution_trace": [],
        "retry_counts": {},
        "retry_summary": {},
        "node_status": {"allocate_traffic": "pending"},
        "recovered_error_count": 0,
    }

    updated = await allocate_traffic(state)

    assert updated["next_step"] == "retry_allocate_traffic"
    assert updated["retry_counts"]["allocate_traffic"] == 1
    assert updated["node_status"]["allocate_traffic"] == "retry_needed"
    assert updated["errors"][-1]["event"] == "attempt_failed"
    assert updated["errors"][-1]["recoverable"] is True


@pytest.mark.anyio
async def test_collect_context_advances_to_allocate_traffic(monkeypatch) -> None:
    class _FakeScalarResult:
        def __init__(self, values):
            self._values = values

        def all(self):
            return self._values

    class _FakeResult:
        def __init__(self, values):
            self._values = values

        def scalars(self):
            return _FakeScalarResult(self._values)

    class _FakeDb:
        def __init__(self, responses):
            self._responses = list(responses)

        async def execute(self, query):
            del query
            return _FakeResult(self._responses.pop(0))

    async def fake_collect_merchant_performance(db, merchants, product_map, yesterday):
        del db, merchants, product_map, yesterday
        return [{"ai_model": "gpt", "rank": 1, "current_price": 100.0, "original_price": 120.0, "stock": 20}]

    monkeypatch.setattr(
        "ai.graph_nodes.collect_context._collect_merchant_performance",
        fake_collect_merchant_performance,
    )

    state = {
        "day": 1,
        "logs": [],
        "execution_trace": [],
        "node_status": {"collect_context": "pending"},
    }
    db = _FakeDb([[type("ProductStub", (), {"ai_model": "gpt"})()], [object()]])

    updated = await collect_context(state, db)

    assert updated["next_step"] == "allocate_traffic"
    assert updated["execution_trace"][-1] == "collect_context"
    assert updated["node_status"]["collect_context"] == "success"
    assert updated["logs"][-1]["node"] == "collect_context"


@pytest.mark.anyio
async def test_retry_allocate_traffic_records_execution_trace_and_logs(monkeypatch) -> None:
    from ai.graph_nodes.allocate_traffic import retry_allocate_traffic

    async def fake_allocate_traffic(state):
        return {
            **state,
            "next_step": "merchant_decision",
            "execution_trace": [*state["execution_trace"], "allocate_traffic"],
            "logs": [*state["logs"], {"node": "allocate_traffic"}],
        }

    monkeypatch.setattr("ai.graph_nodes.allocate_traffic.allocate_traffic", fake_allocate_traffic)

    state = {
        "execution_trace": [],
        "logs": [],
        "retry_counts": {"allocate_traffic": 1},
    }

    updated = await retry_allocate_traffic(state)

    assert updated["execution_trace"][:2] == ["retry_allocate_traffic", "allocate_traffic"]
    assert updated["logs"][0]["node"] == "retry_allocate_traffic"
    assert updated["logs"][0]["retry_count"] == 1


def test_recover_allocate_traffic_halts_when_fallback_is_empty(monkeypatch) -> None:
    from ai.graph_nodes.allocate_traffic import recover_allocate_traffic

    monkeypatch.setattr(
        "ai.graph_nodes.allocate_traffic._fallback_allocate",
        lambda merchants_data, traffic_pool: {"allocations": [], "reasoning": "platform-ai-fallback"},
    )

    state = {
        "merchants_data": [{"ai_model": "gpt"}],
        "traffic_allocations": [],
        "platform_reasoning": "",
        "logs": [],
        "errors": [],
        "execution_trace": [],
        "retry_counts": {"allocate_traffic": 2},
        "retry_summary": {},
        "node_status": {"allocate_traffic": "retry_needed"},
        "recovered_error_count": 0,
        "halt_reason": None,
    }

    updated = recover_allocate_traffic(state)

    assert updated["next_step"] == "halt_day"
    assert updated["halt_reason"] == "platform_allocation_failed"
    assert updated["node_status"]["allocate_traffic"] == "failed"
    assert updated["execution_trace"][-1] == "recover_allocate_traffic"
    assert updated["retry_summary"]["allocate_traffic"] == {
        "attempts": 2,
        "status": "failed",
        "used_fallback": False,
    }
    assert updated["logs"][-1]["node"] == "recover_allocate_traffic"
    assert updated["logs"][-1]["event"] == "fallback_exhausted"


def test_recover_allocate_traffic_records_fallback_recovery(monkeypatch) -> None:
    from ai.graph_nodes.allocate_traffic import recover_allocate_traffic

    monkeypatch.setattr(
        "ai.graph_nodes.allocate_traffic._fallback_allocate",
        lambda merchants_data, traffic_pool: {
            "allocations": [{"merchant_ai": "gpt", "demographic": "youth", "traffic": 8}],
            "reasoning": "platform-ai-fallback",
        },
    )

    state = {
        "merchants_data": [{"ai_model": "gpt"}],
        "traffic_allocations": [],
        "platform_reasoning": "",
        "logs": [],
        "errors": [],
        "execution_trace": [],
        "retry_counts": {"allocate_traffic": 2},
        "retry_summary": {},
        "node_status": {"allocate_traffic": "retry_needed"},
        "recovered_error_count": 0,
        "halt_reason": None,
    }

    updated = recover_allocate_traffic(state)

    assert updated["next_step"] == "merchant_decision"
    assert updated["node_status"]["allocate_traffic"] == "fallback"
    assert updated["recovered_error_count"] == 1
    assert updated["retry_summary"]["allocate_traffic"]["used_fallback"] is True
    assert updated["execution_trace"][-1] == "recover_allocate_traffic"
    assert updated["logs"][-1]["node"] == "recover_allocate_traffic"
    assert updated["logs"][-1]["event"] == "fallback_recovery"


@pytest.mark.anyio
async def test_recover_merchant_decision_uses_safe_fallback_for_failed_merchant(monkeypatch) -> None:
    from ai.graph_nodes.merchant_decision import recover_merchant_decision

    state = {
        "merchants_data": [
            {
                "ai_model": "gpt",
                "current_price": 100.0,
                "original_price": 120.0,
                "stock": 10,
                "rank": 1,
            },
            {
                "ai_model": "qwen",
                "current_price": 80.0,
                "original_price": 100.0,
                "stock": 10,
                "rank": 2,
            },
        ],
        "merchant_decisions": {
            "gpt": {
                "price": 101.0,
                "promotion": "",
                "target_focus": "youth",
                "description_update": "",
                "restock": 0,
                "research_new_product": None,
                "reasoning": "ok",
            }
        },
        "merchant_status": {
            "gpt": {"status": "success"},
            "qwen": {"status": "failed", "attempts": 2},
        },
        "failed_merchants": ["qwen"],
        "logs": [],
        "errors": [],
        "execution_trace": [],
        "recovered_error_count": 0,
        "next_step": "recover_merchant_decision",
    }

    updated = await recover_merchant_decision(state)

    assert updated["merchant_status"]["qwen"]["status"] == "fallback"
    assert updated["merchant_decisions"]["qwen"]["reasoning"] == "fallback decision"
    assert updated["recovered_error_count"] == 1
    assert updated["next_step"] == "validate_decision"


@pytest.mark.anyio
async def test_merchant_decision_routes_to_recovery_when_some_merchants_fail(monkeypatch) -> None:
    from ai.graph_nodes.merchant_decision import merchant_decision

    calls = {"gpt": 0, "qwen": 0}

    async def fake_get_all_decisions(
        db,
        product_map,
        merchants_data,
        allocations,
        day,
        on_ai_complete=None,
    ):
        del db, product_map, allocations, day, on_ai_complete
        ai_model = merchants_data[0]["ai_model"]
        calls[ai_model] += 1
        if ai_model == "gpt":
            return {
                "gpt": {
                    "price": 100.0,
                    "promotion": "",
                    "target_focus": "youth",
                    "description_update": "",
                    "restock": 0,
                    "research_new_product": None,
                    "reasoning": "ok",
                }
            }
        return {}

    monkeypatch.setattr("ai.graph_nodes.merchant_decision._get_all_decisions", fake_get_all_decisions)

    state = {
        "day": 1,
        "product_map": {},
        "traffic_allocations": [],
        "merchants_data": [
            {
                "ai_model": "gpt",
                "current_price": 100.0,
                "original_price": 120.0,
                "stock": 10,
                "rank": 1,
            },
            {
                "ai_model": "qwen",
                "current_price": 80.0,
                "original_price": 100.0,
                "stock": 10,
                "rank": 2,
            },
        ],
        "merchant_decisions": {},
        "merchant_status": {},
        "failed_merchants": [],
        "logs": [],
        "errors": [],
        "execution_trace": [],
    }

    updated = await merchant_decision(state, db=None)

    assert calls["gpt"] == 1
    assert calls["qwen"] == 2
    assert updated["merchant_status"]["gpt"]["status"] == "success"
    assert updated["merchant_status"]["qwen"] == {
        "status": "failed",
        "attempts": 2,
        "recoverable": True,
    }
    assert updated["failed_merchants"] == ["qwen"]
    assert updated["next_step"] == "recover_merchant_decision"


@pytest.mark.anyio
async def test_merchant_decision_sets_specific_halt_reason_when_all_merchants_fail(monkeypatch) -> None:
    from ai.graph_nodes.merchant_decision import merchant_decision

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

    monkeypatch.setattr("ai.graph_nodes.merchant_decision._get_all_decisions", fake_get_all_decisions)

    state = {
        "day": 1,
        "product_map": {},
        "traffic_allocations": [],
        "merchants_data": [
            {
                "ai_model": "gpt",
                "current_price": 100.0,
                "original_price": 120.0,
                "stock": 10,
                "rank": 1,
            }
        ],
        "merchant_decisions": {},
        "merchant_status": {},
        "failed_merchants": [],
        "logs": [],
        "errors": [],
        "execution_trace": [],
        "halt_reason": None,
    }

    updated = await merchant_decision(state, db=None)

    assert updated["next_step"] == "halt_day"
    assert updated["halt_reason"] == "merchant_decision_failed"
    assert updated["failed_merchants"] == ["gpt"]


def test_validate_single_decision_clamps_large_price_jump() -> None:
    merchant_info = {
        "current_price": 100.0,
        "original_price": 120.0,
        "stock": 20,
        "rank": 5,
    }
    decision = {
        "price": 180.0,
        "promotion": "",
        "target_focus": "youth",
        "description_update": "",
        "restock": 0,
        "research_new_product": None,
        "reasoning": "test",
    }

    validated = validate_single_decision("gpt", merchant_info, decision)

    assert validated["validated_decision"]["price"] == 115.0
    assert validated["used_fallback"] is True
    assert "price_out_of_range" in validated["issues"]


def test_validate_decisions_records_fallback_count() -> None:
    from ai.graph_nodes.validate_decision import validate_decisions

    state = {
        "merchants_data": [
            {
                "ai_model": "gpt",
                "current_price": 100.0,
                "original_price": 120.0,
                "stock": 10,
                "rank": 1,
            }
        ],
        "merchant_decisions": {
            "gpt": {
                "price": 180.0,
                "promotion": "",
                "target_focus": "youth",
                "description_update": "",
                "restock": 0,
                "research_new_product": None,
                "reasoning": "bad",
            }
        },
        "logs": [],
        "execution_trace": [],
        "errors": [],
        "retry_summary": {},
        "merchant_status": {},
        "failed_merchants": [],
        "halt_reason": None,
    }

    updated = validate_decisions(state)

    assert updated["validation_results"]["gpt"]["used_fallback"] is True
    assert updated["logs"][-1]["fallback_count"] == 1
    assert updated["retry_summary"]["merchant_decision"] == {
        "failed_merchants": [],
        "fallback_count": 1,
    }
    assert updated["next_step"] == "generate_orders"
    assert updated["execution_trace"][-1] == "validate_decision"


def test_finalize_rankings_sorts_by_units_sold_desc() -> None:
    state = {
        "orders_result": [
            {"merchant_ai": "gpt", "units_sold": 4, "revenue": 100.0},
            {"merchant_ai": "qwen", "units_sold": 9, "revenue": 120.0},
        ],
        "logs": [],
    }

    updated = finalize_rankings(state)

    assert updated["rankings"][0]["merchant_ai"] == "qwen"
    assert updated["rankings"][0]["rank"] == 1
    assert updated["rankings"][1]["rank"] == 2
