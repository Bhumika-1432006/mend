from mend.site import render


def test_site_renders_from_run_files():
    page = render()
    assert "gents that fix themselves, and prove it." in page and 'id="rounds"' in page and 'id="evidence"' in page
