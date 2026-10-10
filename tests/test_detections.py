import mend.detections as det


def test_create_previews_first_and_skips_guards_that_match_nothing(monkeypatch):
    calls = []

    def fake_run(tool, args):
        calls.append(tool)
        if tool == "list_detections":
            return {"detections": []}
        if tool == "preview_detection":
            return {"total_count": 0}
        raise AssertionError(f"unexpected call {tool}")

    monkeypatch.setattr(det, "_run", fake_run)
    guard = {"display_name": "Mend: x", "span_name": "run_tests", "output_pattern": "boom", "description": "d"}
    assert det.create(guard, "g1")["status"].startswith("skipped")
    assert calls == ["list_detections", "preview_detection"]  # never created without a real match


def test_create_uses_span_name_scope_and_regex_on_output(monkeypatch):
    sent = {}

    def fake_run(tool, args):
        if tool == "list_detections":
            return {"detections": [{"display_name": "other"}]}
        if tool == "preview_detection":
            return {"total_count": 4}
        sent.update(args)
        return {"id": "d1"}

    monkeypatch.setattr(det, "_run", fake_run)
    guard = {"display_name": "Mend: x", "span_name": "edit_file", "output_pattern": "not found", "description": "d"}
    result = det.create(guard, "g1")
    assert result == {"guard": "Mend: x", "status": "created", "matched_spans": 4}
    assert sent["run_on"] == {"frequency": "span_name", "span_names": ["edit_file"]}
    assert sent["config"] == {"output_pattern": "not found"} and sent["group_id"] == "g1"
