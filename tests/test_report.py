from mend.report import render


def test_report_renders_rounds_and_task_grid():
    page = render()
    assert "<title>Mend report</title>" in page and "Tasks across runs" in page
