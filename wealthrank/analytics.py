"""Portfolio metrics from observed price/NAV histories; no fabricated market data."""
from datetime import timedelta

import numpy as np
import pandas as pd


PERIODS = {"1W": 7, "1M": 30, "6M": 183, "1Y": 365, "5Y": 1826}


def period_returns(close: pd.Series) -> dict[str, dict | None]:
    """Return None when history cannot cover a window's start date."""
    series = pd.to_numeric(close, errors="coerce").dropna().sort_index()
    if series.empty:
        return {name: None for name in PERIODS}
    series = series[~series.index.duplicated(keep="last")]
    end, last = series.index[-1], float(series.iloc[-1])
    results = {}
    for name, days in PERIODS.items():
        target = end - pd.Timedelta(days=days)
        earlier = series.loc[:target]
        # Never label a 1-year return using just a few months of data.
        tolerance = 5 if days <= 30 else 12 if days <= 183 else 16
        if earlier.empty or (target - earlier.index[-1]).days > tolerance:
            results[name] = None
            continue
        past = float(earlier.iloc[-1])
        if past <= 0:
            results[name] = None
            continue
        elapsed_days = max((end - earlier.index[-1]).days, 1)
        absolute = last / past - 1
        annualized = (last / past) ** (365.25 / elapsed_days) - 1 if days >= 365 else None
        results[name] = {"absolute": absolute, "annualized": annualized}
    return results


def allocation(positions: list[dict]) -> pd.DataFrame:
    rows = [{"Asset": p["name"], "Type": p["asset_class"], "Sector": p.get("sector") or "Unclassified",
             "Value": float(p["value_inr"])} for p in positions if p.get("value_inr", 0) > 0]
    result = pd.DataFrame(rows, columns=["Asset", "Type", "Sector", "Value"])
    if not result.empty:
        result["Weight"] = result["Value"] / result["Value"].sum()
    return result


def risk_metrics(positions: list[dict], benchmark: pd.Series | None = None) -> dict:
    weights_table = allocation(positions)
    if weights_table.empty:
        return {"total": 0.0, "volatility": None, "beta": None,
                "concentration": None, "risk_score": None, "observations": 0,
                "hhi": None, "warnings": ["No holdings with verified market prices."]}
    total = float(weights_table["Value"].sum())
    weights = weights_table["Weight"].to_numpy(dtype=float)
    concentration = float(weights.max())
    hhi = float(np.dot(weights, weights))
    histories = {}
    for idx, p in enumerate(positions):
        hist = p.get("history_inr")
        if p.get("value_inr", 0) > 0 and isinstance(hist, pd.Series) and len(hist) >= 3:
            histories[idx] = pd.to_numeric(hist, errors="coerce").sort_index()
    warnings = []
    volatility = beta = risk_score = None
    observations = 0
    if len(histories) != len(weights_table):
        warnings.append("Some priced holdings lack sufficient history; risk metrics are partial.")
    if histories:
        frame = pd.concat(histories, axis=1).sort_index().ffill(limit=3).dropna()
        if len(frame) >= 61:
            returns = frame.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).dropna()
            if len(returns) >= 60:
                usable_values = np.array([float(positions[i]["value_inr"]) for i in histories])
                usable_weights = usable_values / usable_values.sum()
                portfolio_returns = returns.to_numpy() @ usable_weights
                observations = len(portfolio_returns)
                volatility = float(np.std(portfolio_returns, ddof=1) * np.sqrt(252))
                if benchmark is not None and len(benchmark) > 60:
                    market = pd.to_numeric(benchmark, errors="coerce").sort_index().pct_change(fill_method=None)
                    comparison = pd.concat([pd.Series(portfolio_returns, index=returns.index), market], axis=1).dropna()
                    if len(comparison) >= 60 and comparison.iloc[:, 1].var() > 0:
                        beta = float(comparison.iloc[:, 0].cov(comparison.iloc[:, 1]) /
                                     comparison.iloc[:, 1].var())
                volatility_component = min(volatility / .50, 1)
                concentration_component = max(0, (concentration - .20) / .80)
                if beta is None:
                    risk_score = int(round(100 * (0.67 * volatility_component + 0.33 * concentration_component)))
                else:
                    beta_component = min(abs(beta) / 2, 1)
                    risk_score = int(round(100 * (0.58 * volatility_component +
                                                  0.28 * concentration_component +
                                                  0.14 * beta_component)))
        else:
            warnings.append("At least 60 overlapping daily returns are required for volatility and beta.")
    if volatility is None and not warnings:
        warnings.append("Not enough observations for risk statistics.")
    if concentration > 0.40:
        warnings.append("Largest holding exceeds 40% of priced portfolio value.")
    if beta is None:
        warnings.append("Beta unavailable; market benchmark or overlapping history is insufficient.")
    return {"total": total, "volatility": volatility, "beta": beta,
            "concentration": concentration, "risk_score": risk_score,
            "observations": observations, "hhi": hhi, "warnings": warnings}


def percentage_change(latest: float, basis: float | None) -> float | None:
    if basis is None or basis <= 0:
        return None
    return latest / basis - 1
