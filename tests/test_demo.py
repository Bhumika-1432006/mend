from mend.demo import _steps


def test_steps_flag_whole_file_writes_and_label_full_suite_runs():
    trace = {"tool_calls": [
        {"tool": "write_file", "args": {"path": "a.py", "content": "<9 chars>"}, "output": "wrote a.py"},
        {"tool": "run_tests", "args": {"pattern": ""}, "output": "FAILED\n..."},
        {"tool": "edit_file", "args": {"path": "a.py"}, "output": "edited a.py"},
    ]}
    steps = _steps(trace)
    assert [s["flag"] for s in steps] == ["bad", "bad", "ok"]
    assert steps[1]["detail"] == "full suite" and steps[1]["out"] == "FAILED"
