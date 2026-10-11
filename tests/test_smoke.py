import mend


def test_package_imports():
    assert mend.__doc__


def test_suite_counts_tool_calls_without_changing_the_worker():
    import types
    from mend.suite import count_tool_calls
    worker = types.SimpleNamespace(HANDLERS={"read_file": lambda work, **a: "x", "edit_file": lambda work, **a: "y"})
    counts = {}
    count_tool_calls(worker, counts)
    worker.HANDLERS["read_file"]("w", path="a")
    worker.HANDLERS["read_file"]("w", path="b")
    worker.HANDLERS["edit_file"]("w", path="a")
    assert counts == {"read_file": 2, "edit_file": 1}
