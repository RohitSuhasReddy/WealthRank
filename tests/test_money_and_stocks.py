import numpy as np
import pandas as pd
import pytest

from wealthrank.money import format_inr, parse_inr
from wealthrank.stock_metrics import instrument_metrics, max_drawdown


@pytest.mark.parametrize("written", ["25,00,000", "2,500,000", "2500000", "₹25,00,000"])
def test_accepts_common_comma_formats(written):
    assert parse_inr(written) == 2_500_000


@pytest.mark.parametrize("written", ["25,000,00", "1,2,345", "-100", "inf", "1e8", ""])
def test_rejects_invalid_amounts(written):
    with pytest.raises(ValueError):
        parse_inr(written)


def test_indian_formatting():
    assert format_inr(2500000) == "25,00,000"
    assert format_inr(2500000.5, decimals=True) == "25,00,000.50"


def test_metrics_alpha_beta_and_drawdown():
    dates = pd.bdate_range("2024-01-01", periods=400)
    move = np.sin(np.arange(400) / 16) * .003 + .0008
    market = pd.Series(100 * np.cumprod(1 + move), index=dates)
    instrument = pd.Series(120 * np.cumprod(1 + 1.2 * move), index=dates)
    result = instrument_metrics(instrument, market, risk_free_rate=.06)
    assert result["beta"] == pytest.approx(1.2, rel=.03)
    assert result["alpha"] is not None
    assert result["return_1y"] is not None
    assert result["annual_volatility"] > 0
    assert result["sharpe"] is not None
    assert -1 <= result["max_drawdown"] <= 0
    assert max_drawdown(pd.Series([100, 120, 90], index=pd.date_range("2024-01-01", periods=3))) == pytest.approx(-.25)


def test_metrics_do_not_invent_missing_1y_history():
    dates = pd.bdate_range("2025-01-01", periods=50)
    history = pd.Series(np.linspace(100, 110, 50), index=dates)
    result = instrument_metrics(history)
    assert result["return_1y"] is None
    assert result["beta"] is None
    assert result["alpha"] is None


from wealthrank.data import normalize_holdings


def test_portfolio_accepts_comma_separated_buy_price():
    frame = pd.DataFrame([{"Type": "Stock", "Ticker": "INFY.NS", "Quantity": 3, "Avg Buy Price": "1,250.50"}])
    assert normalize_holdings(frame)[0]["Avg Buy Price"] == pytest.approx(1250.5)


def test_candidate_batch_handles_multi_ticker_download(monkeypatch):
    from wealthrank.data import fetch_stock_batch
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=130)
    symbols = ["INFY.NS", "MSFT"]
    columns = pd.MultiIndex.from_product([symbols, ["Close", "Volume"]])
    frame = pd.DataFrame(index=dates, columns=columns, dtype=float)
    for ticker in symbols:
        frame[(ticker, "Close")] = np.linspace(100, 150, len(dates))
        frame[(ticker, "Volume")] = np.ones(len(dates)) * 2_000_000
    monkeypatch.setattr("wealthrank.data.yf.download", lambda **kwargs: frame)
    values, errors = fetch_stock_batch(symbols)
    assert not errors
    assert [x["ticker"] for x in values] == symbols
    assert values[0]["currency"] == "INR"
    assert values[1]["currency"] == "USD"
    assert len(values[0]["close"]) == 130


def test_ranker_returns_ten_when_ten_pass_screens():
    from wealthrank.recommendations import rank_candidates
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=130)
    closes = pd.Series(100 + 7 * np.sin(np.arange(130) / 10), index=dates)
    universe = [{
        "ticker": f"CANDIDATE{i}.NS", "name": f"Stock {i}", "asset_class": "Stock",
        "sector": "Technology", "currency": "INR", "close": closes,
        "volume": pd.Series([1_000_000] * 130, index=dates),
        "source": "synthetic test fixture", "as_of": str(dates[-1].date()),
    } for i in range(13)]
    holdings = [{"ticker": "SECTOR.NS", "sector": "Consumer", "value_inr": 1000}]
    ranked, excluded = rank_candidates(holdings, universe, "Moderate", mode="Similar", limit=10)
    assert len(ranked) == 10
    assert ranked[0]["score"] >= ranked[-1]["score"]



def test_india_universe_contains_accepted_ampersand_symbol(monkeypatch):
    """Regression: M&M.NS previously crashed *all* recommendations."""
    from wealthrank.data import fetch_stock_batch
    from wealthrank.recommendations import candidate_universe
    import re
    candidates = candidate_universe("INR")
    assert "M&M.NS" in candidates
    assert all(re.fullmatch(r"[A-Z0-9.&\-]{1,24}", symbol) for symbol in candidates)
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=130)
    frame = pd.DataFrame(
        {
            ("M&M.NS", "Close"): np.linspace(100, 150, len(dates)),
            ("M&M.NS", "Volume"): np.full(len(dates), 1_000_000),
            ("INFY.NS", "Close"): np.linspace(200, 275, len(dates)),
            ("INFY.NS", "Volume"): np.full(len(dates), 2_000_000),
        }, index=dates,
    )
    calls = []
    def fake_download(**kwargs):
        calls.append(kwargs["tickers"])
        return frame
    monkeypatch.setattr("wealthrank.data.yf.download", fake_download)
    assets, errors = fetch_stock_batch(["M&M.NS", "INFY.NS"])
    assert not errors
    assert [asset["ticker"] for asset in assets] == ["M&M.NS", "INFY.NS"]
    assert calls == [["M&M.NS", "INFY.NS"]]


def test_bad_candidates_are_skipped_without_crashing(monkeypatch):
    from wealthrank.data import fetch_stock_batch
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=120)
    frame = pd.DataFrame({
        ("INFY.NS", "Close"): np.linspace(90, 110, len(dates)),
        ("INFY.NS", "Volume"): np.full(len(dates), 1_000_000),
    }, index=dates)
    monkeypatch.setattr(
        "wealthrank.data.yf.download",
        lambda **kwargs: frame if kwargs["tickers"] == ["INFY.NS"] else None,
    )
    assets, errors = fetch_stock_batch(["NOT VALID!", "INFY.NS"])
    assert [asset["ticker"] for asset in assets] == ["INFY.NS"]
    assert len(errors) == 1
    assert "NOT VALID!" in errors[0]


def test_single_stock_accepts_ampersand_ticker(monkeypatch):
    from wealthrank.data import fetch_stock
    dates = pd.bdate_range(end=pd.Timestamp.now().normalize(), periods=120, tz="UTC")
    frame = pd.DataFrame({"Close": np.linspace(100, 150, len(dates)),
                          "Volume": np.full(len(dates), 500000)}, index=dates)
    class FakeTicker:
        fast_info = {"currency": "INR"}
        def history(self, **kwargs):
            return frame
    monkeypatch.setattr("wealthrank.data.yf.Ticker", lambda name: FakeTicker())
    asset = fetch_stock("M&M.NS")
    assert asset["ticker"] == "M&M.NS"
    assert asset["currency"] == "INR"
