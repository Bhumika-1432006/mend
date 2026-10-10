from mend.site import render


def test_site_renders_from_run_files():
    page = render()
    assert "Agents that fix themselves" in page and 'id="rounds"' in page and 'id="evidence"' in page
