from mend.tasks import check


def test_every_planted_bug_breaks_the_sandbox_and_correct_code_passes():
    assert check()
