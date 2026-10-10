from mend.supervisor import trace_digest


def test_trace_digest_lists_tree_then_truncated_span_io():
    trace = {"spans": [
        {"span_id": "a", "parent_span_id": "", "type": "workflow", "name": "solve_task", "status": "SUCCESS", "duration_ms": 10},
        {"span_id": "b", "parent_span_id": "a", "type": "tool_call", "name": "run_tests", "status": "SUCCESS",
         "duration_ms": 5, "input_value": "{}", "output_value": "FAILED " + "x" * 5000},
    ]}
    text = trace_digest(trace)
    assert text.startswith("workflow solve_task [SUCCESS] 10ms\n  tool_call run_tests")
    assert "out: FAILED x" in text and len(text) < 1200


def test_rounds_chain_kept_runs_and_stop_at_first_revert(monkeypatch):
    import mend.supervisor as sup
    outcomes = iter([True, True, False, True])
    seen = []

    def fake_round(run_id):
        seen.append(run_id)
        return {"kept": next(outcomes), "after": run_id + "+"}

    monkeypatch.setattr(sup, "one_round", fake_round)
    records = sup.rounds("r0", limit=5)
    assert seen == ["r0", "r0+", "r0++"] and [r["kept"] for r in records] == [True, True, False]
