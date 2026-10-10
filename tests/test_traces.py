from mend.traces import span_lines


def test_span_lines_nests_children_under_parents():
    trace = {"spans": [
        {"span_id": "b", "parent_span_id": "a", "type": "llm", "name": "claude", "status": "ERROR", "duration_ms": 871.2},
        {"span_id": "a", "parent_span_id": "", "type": "workflow", "name": "solve", "status": "ERROR", "duration_ms": 890.0},
    ]}
    assert span_lines(trace) == ["workflow solve [ERROR] 890ms", "  llm claude [ERROR] 871ms"]
