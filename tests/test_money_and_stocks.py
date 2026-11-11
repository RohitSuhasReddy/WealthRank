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
