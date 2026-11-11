"""Category ranking, chart scaling and sample portfolio regression checks."""
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from wealthrank.catalog import MARKET_SECTORS, sector_map, sectors_for_market, tickers_for_sector
from wealthrank.category_ranking import rank_sector_stocks
from wealthrank.charts import performance_chart, fire_projection_chart
from wealthrank.data import STOCK_SECTORS, normalize_holdings
from wealthrank.fire import FireInputs, project_fire


def test_every_sector_has_at_least_ten_curated_candidates():
    known = sector_map()
    for market, categories in MARKET_SECTORS.items():
        assert categories
        assert set(sectors_for_market(market)) == set(categories)
        for name, tickers in categories.items():
            assert len(tickers) >= 10, (market, name)
            assert len(set(tickers)) == len(tickers)
            assert list(tickers_for_sector(market, name)) == list(tickers)
            assert all(known[ticker] == name for ticker in tickers)
            assert all(STOCK_SECTORS[ticker] == name for ticker in tickers)
    assert "SPCX" in tickers_for_sector("US", "Aerospace & Defense")
    assert {"IONQ", "QBTS"}.issubset(tickers_for_sector("US", "Technology"))


def test_sector_ranking_orders_up_to_ten_without_hiding_risk_flags():
    dates = pd.bdate_range("2025-01-01", periods=300)
    candidates = []
    for i in range(13):
        wave = np.sin(np.arange(300) / (11 + i)) * (5 + i * 1.2)
        prices = pd.Series(100 + np.arange(300) * .07 + wave, index=dates)
        candidates.append({
            "ticker": f"S{i}.NS", "name": f"Stock {i}", "sector": "Healthcare",
            "asset_class": "Stock", "currency": "INR", "close": prices,
            "volume": pd.Series(np.full(300, 600_000), index=dates),
            "source": "test fixture", "as_of": str(dates[-1].date()),
        })
    ranked, skipped = rank_sector_stocks([], candidates, "Healthcare", "Conservative")
    assert len(ranked) == 10
    assert ranked[0]["score"] >= ranked[-1]["score"]
    assert all(x["sector"] == "Healthcare" for x in ranked)
    assert all(x["ticker"] in {x["ticker"] for x in candidates} for x in ranked)
    assert all(isinstance(item["flags"], list) for item in ranked)
    # An existing holding is never shown as a discovery result.
    held = [{"ticker": ranked[0]["ticker"], "sector": "Healthcare", "value_inr": 10000}]
    new_ranked, new_skipped = rank_sector_stocks(held, candidates, "Healthcare", "Conservative")
    assert len(new_ranked) == 10
    assert ranked[0]["ticker"] not in {x["ticker"] for x in new_ranked}
    assert any("already in portfolio" in message for message in new_skipped)


def test_price_chart_zooms_to_observed_range_not_zero():
    dates = pd.bdate_range("2026-10-05", periods=26)
    prices = pd.Series(100 + np.sin(np.arange(26) / 3) * 2.2, index=dates)
    asset = {"close": prices, "currency": "USD"}
    fig = performance_chart(asset, "1M")
    lo, hi = fig.layout.yaxis.range
    assert lo > 85
    assert hi < 115
    assert fig.layout.yaxis.autorange is False
    assert not any(getattr(trace, "fill", None) == "tozeroy" for trace in fig.data)


def test_percentage_change_chart_rebases_period_start():
    dates = pd.bdate_range("2026-10-20", periods=13)
    values = pd.Series(np.linspace(100, 110, len(dates)), index=dates)
    fig = performance_chart({"close": values, "currency": "INR"}, "1M", view="Percentage change")
    assert float(fig.data[0].y[0]) == pytest.approx(0)
    assert float(fig.data[0].y[-1]) == pytest.approx(10)
    assert fig.layout.yaxis.range[0] < 0 < fig.layout.yaxis.range[1]
    with pytest.raises(ValueError):
        performance_chart({"close": values, "currency": "INR"}, "1M", view="Misleading")


def test_fire_chart_uses_readable_rupee_units():
    base = FireInputs(30, 50000, 1000000, .10, .06, 25000)
    projection, _ = project_fire(base, years=30)
    shorter = projection.loc[projection["Age"] <= 60]
    fig = fire_projection_chart(shorter, 55)
    assert "₹" in fig.layout.yaxis.title.text
    assert len(fig.data) == 3


def test_demo_sized_portfolio_with_dates_is_accepted():
    frame = pd.DataFrame([
        {"Type": "Stock", "Ticker": f"S{i}.NS",
         "Quantity": i+1, "Avg Buy Price": None,
         "Purchase Date": "2025-08-20"}
        for i in range(18)
    ] + [
        {"Type": "Mutual fund", "Ticker": str(140000+i),
         "Quantity": 12.5+i, "Avg Buy Price": None,
         "Purchase Date": datetime(2025, 3, 12)}
        for i in range(4)
    ])
    rows = normalize_holdings(frame)
    assert len(rows) == 22
    assert rows[0]["Purchase Date"] == "2025-08-20"
    assert rows[-1]["Purchase Date"] == "2025-03-12"
    with pytest.raises(ValueError):
        normalize_holdings(frame.assign(**{"Purchase Date":"2099-01-01"}))
