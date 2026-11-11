"""Top-ten sector ranking with explicit risk/quality annotations.

Unlike the strict portfolio guardrail filter, the category explorer ranks a
sector's observed stocks and marks risks instead of silently suppressing them.
This is a *relevance score*, not an investment-return prediction.
"""
from __future__ import annotations

import math
import numpy as np

from wealthrank.recommendations import (
    RISK_CAP, RISK_TARGET, candidate_volatility, _liquidity_check,
)


def rank_sector_stocks(
    portfolio: list[dict],
    candidates: list[dict],
    sector: str,
    risk_preference: str,
    limit: int = 10,
) -> tuple[list[dict], list[str]]:
    if risk_preference not in RISK_TARGET:
        raise ValueError("Unknown risk preference")
    if not 1 <= limit <= 50:
        raise ValueError("Limit must be between 1 and 50.")
    held = {str(a["ticker"]).upper() for a in portfolio}
    total = sum(max(0.0, float(a.get("value_inr", 0))) for a in portfolio)
    weight = (sum(float(a.get("value_inr", 0)) for a in portfolio
                  if a.get("sector") == sector) / total) if total else 0.0

    output, skipped = [], []
    for asset in candidates:
        ticker = str(asset.get("ticker", "")).upper()
        if asset.get("sector") != sector:
            skipped.append(f"{ticker}: not part of the chosen category")
            continue
        if ticker in held:
            skipped.append(f"{ticker}: already in portfolio")
            continue
        close = asset.get("close")
        if close is None or len(close) < 61:
            skipped.append(f"{ticker}: fewer than 61 observed close prices")
            continue
        volatility = candidate_volatility(asset)
        if volatility is None or not math.isfinite(volatility):
            skipped.append(f"{ticker}: insufficient return history")
            continue

        liquidity_ok, liquidity_note = _liquidity_check(asset)
        close_values = np.asarray(close, dtype=float)
        if len(close_values) >= 250 and close_values[-250] > 0:
            one_year_return = float(close_values[-1] / close_values[-250] - 1)
        else:
            one_year_return = None
        risk_fit = max(0., 1 - abs(volatility - RISK_TARGET[risk_preference]) / .75)
        history_fit = min(1., len(close_values) / 252)
        momentum_fit = (0.5 if one_year_return is None else
                        float(np.clip((one_year_return + .30) / .90, 0, 1)))
        score = 100 * (.61 * risk_fit + .17 * float(liquidity_ok)
                       + .12 * history_fit + .10 * momentum_fit)

        flags = []
        if volatility > RISK_CAP[risk_preference]:
            flags.append("Volatility exceeds risk preference")
            score -= 18
        if not liquidity_ok:
            flags.append(liquidity_note)
            score -= 13
        if weight > .45:
            flags.append(f"Portfolio already has {weight:.0%} in {sector}")
            score -= 8
        output.append({
            "ticker": ticker, "name": asset.get("name", ticker),
            "sector": sector, "asset_class": "Stock",
            "score": round(float(np.clip(score, 0, 100)), 1),
            "volatility": volatility, "liquidity_note": liquidity_note,
            "explanation": ("Risk-aligned observed profile" if not flags
                             else "Shown for comparison; review risk flags"),
            "flags": flags, "as_of": asset.get("as_of", ""),
            "source": asset.get("source", ""),
        })
    output.sort(key=lambda a: (-a["score"], a["ticker"]))
    return output[:limit], skipped
