import mend.verify as v


def test_verify_passes_on_the_committed_readme():
    assert v.main() == 0


def test_verify_fails_when_a_readme_number_is_edited(monkeypatch):
    first = v.expected_strings(v.runs())[0]
    monkeypatch.setattr(v, "README", v.README.replace(first, "99 → 99 / 99"))
    assert v.main() == 1
