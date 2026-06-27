import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ai.graph_state import build_initial_day_state


def test_build_initial_day_state_has_expected_defaults() -> None:
    state = build_initial_day_state(day=3)

    assert state["day"] == 3
    assert state["merchants_data"] == []
    assert state["traffic_allocations"] == []
    assert state["merchant_decisions"] == {}
    assert state["orders_result"] == []
    assert state["rankings"] == []
    assert state["suggestions"] == []
    assert state["platform_reasoning"] == ""
    assert state["logs"] == []
    assert state["errors"] == []
    assert state["execution_path"] == "langgraph"


def test_build_initial_day_state_has_graph_runtime_fields() -> None:
    state = build_initial_day_state(day=3)

    assert state["next_step"] == "collect_context"
    assert state["halt_reason"] is None
    assert state["graph_version"] == "phase3"
    assert state["execution_trace"] == []


def test_build_initial_day_state_has_phase3_recovery_defaults() -> None:
    state = build_initial_day_state(day=5)

    assert state["halted"] is False
    assert state["recovered_error_count"] == 0
    assert state["failed_merchants"] == []
    assert state["retry_counts"] == {}
    assert state["retry_summary"] == {}
    assert state["merchant_status"] == {}
    assert state["node_status"]["collect_context"] == "pending"
    assert state["node_status"]["allocate_traffic"] == "pending"
