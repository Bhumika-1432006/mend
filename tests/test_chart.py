from mend.chart import dumbbell


def test_dumbbell_marks_reverted_rounds_without_relying_on_color():
    rounds = [
        {"kept": True, "before_tokens": 900, "after_tokens": 800, "before_passed": 27, "after_passed": 28, "total": 28},
        {"kept": False, "before_tokens": 500, "after_tokens": 520, "before_passed": 29, "after_passed": 29, "total": 29},
    ]
    svg = dumbbell(rounds)
    assert svg.count("<g>") == 2 and ">reverted<" in svg and 'stroke-dasharray="5 4"' in svg
    assert "-11.1%" in svg and "+4.0%" in svg
