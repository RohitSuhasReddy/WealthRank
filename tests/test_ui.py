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


def test_portfolio_draft_survives_visiting_discover_and_analytics():
    at = AppTest.from_file("../app.py", default_timeout=30).run()
    assert len(at.exception) == 0
    at.session_state["portfolio_draft"] = [
        {
            "Type": "Stock", "Ticker": "AAPL", "Quantity": 7.0,
            "Avg Buy Price": 0.0, "Purchase Date": "2025-04-15",
        },
        {
            "Type": "Stock", "Ticker": "TSLA", "Quantity": 4.0,
            "Avg Buy Price": 0.0, "Purchase Date": "2025-08-03",
        },
    ]
    at.button(key="orbit_portfolio").click().run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    assert {r["Ticker"] for r in at.session_state["portfolio_draft"]} == {"AAPL", "TSLA"}
    at.button(key="nav_discover").click().run()
    assert len(at.exception) == 0
    at.button(key="nav_analytics").click().run()
    assert len(at.exception) == 0
    at.button(key="nav_portfolio").click().run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    assert {r["Ticker"] for r in at.session_state["portfolio_draft"]} == {"AAPL", "TSLA"}
    assert not any(
        r["Ticker"] in {"RELIANCE.NS", "INFY.NS", "ICICIBANK.NS"}
        for r in at.session_state["portfolio_draft"]
    )


def test_successful_analyse_navigates_directly_to_analytics(monkeypatch):
    import numpy as np
    import pandas as pd
    import yfinance

    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=190, tz="UTC")
    frame = pd.DataFrame(
        {"Close": np.linspace(100, 130, len(dates)),
         "Volume": np.full(len(dates), 3_000_000)}, index=dates
    )

    class FakeTicker:
        fast_info = {"currency": "INR"}
        def history(self, **_kwargs):
            return frame

    monkeypatch.setattr(yfinance, "Ticker", lambda _symbol: FakeTicker())
    at = AppTest.from_file("../app.py", default_timeout=45).run()
    at.session_state["portfolio_draft"] = [
        {"Type": "Stock", "Ticker": "MOCKFUNDAMENTAL.NS", "Quantity": 5.0,
         "Avg Buy Price": 0.0, "Purchase Date": "2025-03-14"},
    ]
    at.button(key="orbit_portfolio").click().run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    at.button(key="analyse_portfolio").click().run()
    assert len(at.exception) == 0, [str(exc.message) for exc in at.exception]
    assert at.session_state["active_page"] == "analytics"
    assert len(at.session_state["positions"]) == 1
    assert at.session_state["positions"][0]["ticker"] == "MOCKFUNDAMENTAL.NS"
