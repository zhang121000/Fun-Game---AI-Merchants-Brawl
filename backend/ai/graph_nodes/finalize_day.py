from langsmith import traceable


@traceable(name="graph_node_finalize_day", run_type="chain")
def finalize_rankings(state):
    rankings = sorted(
        state["orders_result"],
        key=lambda item: item["units_sold"],
        reverse=True,
    )
    for index, row in enumerate(rankings, start=1):
        row["rank"] = index
    execution_trace = [*state.get("execution_trace", []), "finalize_day"]

    return {
        **state,
        "rankings": rankings,
        "next_step": "end",
        "halt_reason": "completed",
        "execution_trace": execution_trace,
        "logs": [
            *state["logs"],
            {
                "node": "finalize_day",
                "ranking_count": len(rankings),
            },
        ],
    }
