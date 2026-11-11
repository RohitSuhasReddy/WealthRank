"""Smoke-test the initial Streamlit screen without contacting any market API."""
from streamlit.testing.v1 import AppTest


def test_initial_interface_renders_without_market_data():
    # AppTest paths are relative to this test file's directory.
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
