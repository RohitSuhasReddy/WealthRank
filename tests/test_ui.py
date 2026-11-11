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


def test_fire_switch_between_typed_values_and_sliders():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    at.button(key="orbit_fire").click().run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    at.number_input(key="fire_control_age_typed").set_value(38).run()
    assert len(at.exception) == 0
    assert at.session_state["fire_canonical_age"] == 38
    at.radio(key="fire_control_mode").set_value("Quick sliders").run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    assert at.slider(key="fire_control_age_slider").value == 38


def test_net_worth_direct_entry_does_not_add_portfolio_twice():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    at.button(key="orbit_portfolio").click().run()
    at.radio(key="networth_method").set_value("Enter one total directly").run()
    at.text_input(key="nw_total_manual").set_value("32,50,000").run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    assert at.session_state["net_worth_total"] == 3_250_000
    at.button(key="nav_fire").click().run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    assert "Total net worth" in at.radio(key="fire_capital_source").options
