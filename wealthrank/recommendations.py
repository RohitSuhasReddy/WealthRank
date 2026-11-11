"""Explainable content-based recommendations with explicit risk/sector/liquidity screens."""
from __future__ import annotations

import numpy as np
import pandas as pd


INDIAN_CANDIDATES = [
    "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "ITC.NS", "LT.NS", "SUNPHARMA.NS", "MARUTI.NS",
    "SBIN.NS", "HINDUNILVR.NS",
]
US_CANDIDATES = ["MSFT", "AAPL", "JNJ", "JPM", "XOM", "PG", "AMZN", "NVDA"]
FUND_QUERIES = [
    "UTI Nifty 50 Index Fund",
    "Parag Parikh Flexi Cap Fund",
    "HDFC Balanced Advantage Fund",
]
RISK_TARGET = {"Conservative": .15, "Moderate": .27, "Aggressive": .44}
RISK_CAP = {"Conservative": .30, "Moderate": .52, "Aggressive": .90}
MAX_POST_SECTOR_WEIGHT = .45
PROPOSED_ALLOCATION = .10


def candidate_volatility(asset: dict) -> float | None:
    close = asset.get("history_inr", asset.get("close"))
    if close is None or len(close) < 61:
        return None
    rets = pd.to_numeric(close, errors="coerce").pct_change(fill_method=None)
    rets = rets.replace([np.inf, -np.inf], np.nan).dropna()
    if len(rets) < 60:
        return None
    return float(rets.std(ddof=1) * np.sqrt(252))


def _liquidity_check(asset: dict) -> tuple[bool, str]:
    if asset.get("asset_class") == "Mutual fund":
        # No trading volume for funds; do not claim they passed a liquidity test.
        return True, "Fund liquidity not verified; check exit loads and redemption terms"
    vol = asset.get("volume")
    if vol is None or len(vol) < 15:
        return False, "Missing recent volume history"
    median = float(pd.to_numeric(vol, errors="coerce").tail(20).median())
    last_price = float(asset["close"].iloc[-1])
    trading_value = median * last_price
    threshold = 10_000_000 if asset["currency"] == "INR" else 1_000_000
    if not np.isfinite(trading_value) or trading_value < threshold:
        return False, "Below minimum 20-day median traded-value screen"
    return True, "Recent traded-value screen passed (estimate)"


def rank_candidates(
    portfolio: list[dict],
    candidates: list[dict],
    risk_preference: str,
    mode: str = "Diversifying",
    limit: int = 5,
    preferred_sectors: list[str] | None = None,
) -> tuple[list[dict], list[str]]:
    if risk_preference not in RISK_TARGET:
        raise ValueError("Unknown risk preference.")
    if mode not in {"Diversifying", "Similar"}:
        raise ValueError("Mode must be Similar or Diversifying.")
    total = sum(p["value_inr"] for p in portfolio)
    held = {p["ticker"].upper() for p in portfolio}
    sectors = {}
    for p in portfolio:
        s = p.get("sector", "Unclassified")
        sectors[s] = sectors.get(s, 0) + p["value_inr"] / total if total else 0
    found, excluded = [], []
    for asset in candidates:
        ticker = asset["ticker"].upper()
        if ticker in held:
            continue
        vol = candidate_volatility(asset)
        if vol is None:
            excluded.append(f"{ticker}: insufficient risk history")
            continue
        if vol > RISK_CAP[risk_preference]:
            excluded.append(f"{ticker}: volatility exceeds {risk_preference.lower()} band")
            continue
        liquidity_passed, liquidity_note = _liquidity_check(asset)
        if not liquidity_passed:
            excluded.append(f"{ticker}: {liquidity_note}")
            continue
        sector = asset.get("sector") or "Unclassified"
        current_sector = sectors.get(sector, 0)
        projected_sector = current_sector * (1 - PROPOSED_ALLOCATION) + PROPOSED_ALLOCATION
        if sector != "Unclassified" and projected_sector > MAX_POST_SECTOR_WEIGHT:
            excluded.append(f"{ticker}: proposed sector weight exceeds 45% cap")
            continue
        sector_match = sector in sectors and sector != "Unclassified"
        relevant = sector_match if mode == "Similar" else not sector_match
        risk_fit = max(0., 1 - abs(vol - RISK_TARGET[risk_preference]) / .65)
        preference = .5 if not preferred_sectors else float(sector in preferred_sectors)
        score = .52 * risk_fit + .31 * int(relevant) + .09 * min(1, 1 - current_sector) + .08 * preference
        reason = (
            "Shares an existing exposure" if mode == "Similar" and sector_match
            else "Adds a different sector/category" if mode == "Diversifying" and not sector_match
            else "Risk-fit candidate with a complementary profile"
        )
        found.append({
            "ticker": ticker, "name": asset["name"], "sector": sector,
            "asset_class": asset["asset_class"], "score": float(score * 100),
            "volatility": vol, "liquidity_note": liquidity_note,
            "explanation": reason, "source": asset.get("source", ""),
            "as_of": asset.get("as_of", ""),
        })
    return sorted(found, key=lambda a: (-a["score"], a["ticker"]))[:limit], excluded


def candidate_universe(currency: str) -> list[str]:
    return (INDIAN_CANDIDATES if currency == "INR" else US_CANDIDATES)


def select_fund_search_result(matches: list[dict]) -> str | None:
    """Prefer a DIRECT + GROWTH plan, never an IDCW/dividend or regular plan."""
    eligible = []
    for item in matches:
        label = str(item.get("schemeName", "")).lower()
        if "direct" in label and "growth" in label and not any(
            bad in label for bad in ("idcw", "dividend", "regular")
        ):
            eligible.append(item)
    return str(eligible[0]["schemeCode"]) if eligible else None
