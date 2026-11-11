"""Observed equity/fund metrics with consistent benchmark and currency assumptions.

Statistics use the latest twelve months of overlapping trading-day CLOSES.
Alpha = annualized realized return minus CAPM-expected return, with the
risk-free assumption stated beside the metric. None means insufficient data.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd


def _clean(series: pd.Series) -> pd.Series:
    result = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    index = pd.to_datetime(result.index, utc=True).tz_convert(None).normalize()
    result = pd.Series(result.to_numpy(), index=index).dropna().sort_index()
    return result[~result.index.duplicated(keep="last")]


def max_drawdown(close: pd.Series) -> float | None:
    series = _clean(close)
    if len(series) < 2 or (series <= 0).any():
        return None
    return float((series / series.cummax() - 1).min())


def instrument_metrics(
    close: pd.Series,
    benchmark: pd.Series | None = None,
    risk_free_rate: float = .06,
) -> dict[str, float | int | None]:
    if not -1 < risk_free_rate < 1:
        raise ValueError("Risk-free annual rate should be between -100% and 100%.")
    s = _clean(close)
    empty = {
        "return_1y": None, "cagr_5y": None, "annual_volatility": None,
        "beta": None, "alpha": None, "sharpe": None,
        "max_drawdown": None, "benchmark_1y": None,
        "observations": 0, "risk_free_rate": risk_free_rate,
    }
    if len(s) < 2 or (s <= 0).any():
        return empty

    latest_date = s.index[-1]
    start_1y = latest_date - pd.Timedelta(days=365)
    prior = s.loc[:start_1y]
    if not prior.empty and (start_1y - prior.index[-1]).days <= 15:
        start = prior.index[-1]
        annual_window = s.loc[start:latest_date]
        elapsed_days = (latest_date - start).days
        if elapsed_days >= 330:
            empty["return_1y"] = float(annual_window.iloc[-1] / annual_window.iloc[0] - 1)
    # Five-year CAGR is shown only with near-complete 5-year history.
    target_5y = latest_date - pd.Timedelta(days=365.25 * 5)
    old = s.loc[:target_5y + pd.Timedelta(days=15)]
    if not old.empty:
        start_5y = old.index[0] if len(old) == 1 else old.index[-1]
        elapsed_years = (latest_date - start_5y).days / 365.25
        if 4.75 <= elapsed_years <= 5.15:
            empty["cagr_5y"] = float((s.iloc[-1] / s.loc[start_5y]) ** (1 / elapsed_years) - 1)

    trailing = s.loc[s.index >= latest_date - pd.Timedelta(days=375)]
    if len(trailing) >= 61:
        daily = trailing.pct_change(fill_method=None).dropna()
        if len(daily) >= 60:
            empty["annual_volatility"] = float(daily.std(ddof=1) * math.sqrt(252))
            empty["max_drawdown"] = max_drawdown(trailing)
            empty["observations"] = len(daily)
            if empty["return_1y"] is not None and empty["annual_volatility"] > 0:
                empty["sharpe"] = (empty["return_1y"] - risk_free_rate) / empty["annual_volatility"]

    if benchmark is not None and len(benchmark):
        b = _clean(benchmark)
        if (b <= 0).any():
            return empty
        combined = pd.concat([s.rename("stock"), b.rename("benchmark")], axis=1)
        # Only dates when both were observed: no interpolated benchmark moves.
        combined = combined.dropna().sort_index()
        combined = combined.loc[combined.index >= latest_date - pd.Timedelta(days=375)]
        if len(combined) >= 180 and (combined.index[-1] - combined.index[0]).days >= 330:
            paired = combined.pct_change(fill_method=None).dropna()
            if len(paired) >= 175 and paired["benchmark"].var() > 0:
                empty["beta"] = float(paired["stock"].cov(paired["benchmark"]) / paired["benchmark"].var())
                elapsed_years = (combined.index[-1] - combined.index[0]).days / 365.25
                r_stock = float((combined["stock"].iloc[-1] / combined["stock"].iloc[0]) ** (1 / elapsed_years) - 1)
                r_market = float((combined["benchmark"].iloc[-1] / combined["benchmark"].iloc[0]) ** (1 / elapsed_years) - 1)
                empty["benchmark_1y"] = r_market
                empty["alpha"] = r_stock - (risk_free_rate + empty["beta"] * (r_market - risk_free_rate))
    return empty
