"""Smoke-test the initial Streamlit screen without contacting any market API."""
from streamlit.testing.v1 import AppTest


def test_initial_interface_renders_without_market_data():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]


def test_solar_menu_navigates_without_losing_session():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert len(at.exception) == 0
    at.button(key="orbit_portfolio").click().run()
    assert len(at.exception) == 0, [str(x.message) for x in at.exception]
    assert at.session_state["active_page"] == "portfolio"
    at.button(key="nav_fire").click().run()
    assert len(at.exception) == 0, [str(x.message) for x in at.exception]
    assert at.session_state["active_page"] == "fire"
    # FIRE renders only on its own page; no market fetch needed.
