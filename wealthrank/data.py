"""Free public market-data adapters. Exceptions are surfaced, never replaced by fake quotes."""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
import yfinance as yf

from wealthrank.money import parse_inr


MF_API = "https://api.mfapi.in"
REQUEST_TIMEOUT = 14
STOCK_SECTORS = {
    "RELIANCE.NS": "Energy", "INFY.NS": "Technology",
    "TCS.NS": "Technology", "HDFCBANK.NS": "Financials",
    "ICICIBANK.NS": "Financials", "BHARTIARTL.NS": "Telecom",
    "ITC.NS": "Consumer", "LT.NS": "Industrials",
    "HINDUNILVR.NS": "Consumer", "SBIN.NS": "Financials",
    "SUNPHARMA.NS": "Healthcare", "MARUTI.NS": "Automotive",
    "AAPL": "Technology", "MSFT": "Technology",
    "NVDA": "Technology", "AMZN": "Consumer",
    "JNJ": "Healthcare", "JPM": "Financials",
    "XOM": "Energy", "PG": "Consumer",
    "WIPRO.NS": "Technology", "HCLTECH.NS": "Technology", "TECHM.NS": "Technology",
    "PERSISTENT.NS": "Technology", "COFORGE.NS": "Technology",
    "AXISBANK.NS": "Financials", "KOTAKBANK.NS": "Financials", "BAJFINANCE.NS": "Financials",
    "BAJAJFINSV.NS": "Financials", "INDUSINDBK.NS": "Financials",
    "TITAN.NS": "Consumer", "NESTLEIND.NS": "Consumer", "ASIANPAINT.NS": "Consumer",
    "DABUR.NS": "Consumer", "BRITANNIA.NS": "Consumer",
    "DRREDDY.NS": "Healthcare", "CIPLA.NS": "Healthcare", "APOLLOHOSP.NS": "Healthcare",
    "TATAMOTORS.NS": "Automotive", "M&M.NS": "Automotive", "EICHERMOT.NS": "Automotive",
    "ULTRACEMCO.NS": "Materials", "JSWSTEEL.NS": "Materials", "TATASTEEL.NS": "Materials",
    "NTPC.NS": "Utilities", "POWERGRID.NS": "Utilities", "ONGC.NS": "Energy",
    "COALINDIA.NS": "Energy", "ADANIPORTS.NS": "Industrials", "BEL.NS": "Industrials",
    "SIEMENS.NS": "Industrials",
    "GOOGL": "Technology", "META": "Technology", "ORCL": "Technology",
    "CRM": "Technology", "ADBE": "Technology", "AVGO": "Technology",
    "INTC": "Technology", "AMD": "Technology", "CSCO": "Technology",
    "BAC": "Financials", "V": "Financials", "MA": "Financials",
    "UNH": "Healthcare", "ABBV": "Healthcare", "PFE": "Healthcare",
    "WMT": "Consumer", "COST": "Consumer", "HD": "Consumer",
    "KO": "Consumer", "PEP": "Consumer", "DIS": "Communication",
    "CVX": "Energy", "CAT": "Industrials", "GE": "Industrials",
}


def _series(values: pd.Series) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce")
    index = pd.to_datetime(values.index, errors="coerce", utc=True)
    result = pd.Series(values.to_numpy(), index=index.tz_convert(None).normalize())
    result = result[~result.index.isna()]
    return result[~result.index.duplicated(keep="last")].dropna().sort_index()


def fetch_stock(ticker: str) -> dict:
    symbol = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z0-9^.=&\-]{1,24}", symbol):
        raise ValueError(f"Invalid equity ticker: {ticker!r}")
    asset = yf.Ticker(symbol)
    frame = asset.history(period="5y", interval="1d", auto_adjust=True)
    if frame is None or frame.empty or "Close" not in frame:
        raise ValueError(f"No stock price history for {symbol}. Verify the Yahoo Finance ticker.")
    close = _series(frame["Close"])
    volume = _series(frame["Volume"]) if "Volume" in frame else pd.Series(dtype=float)
    if close.empty or float(close.iloc[-1]) <= 0:
        raise ValueError(f"No usable latest close for {symbol}.")
    currency = "INR" if symbol.endswith((".NS", ".BO")) else "USD"
    # Detect unsupported currencies rather than silently calling them USD.
    try:
        reported = asset.fast_info.get("currency")
        if reported:
            currency = str(reported).upper()
    except Exception:
        pass
    if currency not in {"INR", "USD"}:
        raise ValueError(f"Unsupported currency {currency} for {symbol}; only INR / USD are converted.")
    return {
        "ticker": symbol, "name": symbol, "asset_class": "Stock",
        "sector": STOCK_SECTORS.get(symbol, "Unclassified"),
        "currency": currency, "close": close, "volume": volume,
        "source": "Yahoo Finance", "as_of": close.index[-1].date().isoformat(),
    }


def search_funds(query: str) -> list[dict]:
    query = query.strip()
    if len(query) < 3:
        return []
    resp = requests.get(f"{MF_API}/mf/search", params={"q": query},
                        timeout=REQUEST_TIMEOUT, headers={"User-Agent": "WealthRank/0.1"})
    resp.raise_for_status()
    results = resp.json()
    if not isinstance(results, list):
        raise ValueError("Unexpected mutual-fund search response.")
    return results


def resolve_fund_code(identifier: str) -> str:
    value = str(identifier).strip()
    if value.isdigit():
        return value
    matches = search_funds(value)
    if not matches:
        raise ValueError(f"Mutual fund not found: {value}. Try an AMFI scheme code.")
    phrase = value.casefold()
    exact = [m for m in matches if str(m.get("schemeName", "")).casefold() == phrase]
    if len(exact) == 1:
        return str(exact[0]["schemeCode"])
    if len(matches) == 1:
        return str(matches[0]["schemeCode"])
    raise ValueError(
        f"Multiple funds match {value!r}. Use a specific AMFI scheme code to avoid selecting the wrong plan."
    )


def fetch_fund(identifier: str) -> dict:
    code = resolve_fund_code(identifier)
    response = requests.get(f"{MF_API}/mf/{code}", timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": "WealthRank/0.1"})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not payload.get("data"):
        raise ValueError(f"No NAV data for scheme {code}.")
    meta = payload.get("meta") or {}
    values = pd.DataFrame(payload["data"])
    dates = pd.to_datetime(values["date"], format="%d-%m-%Y", errors="coerce")
    nav = pd.to_numeric(values["nav"], errors="coerce")
    close = pd.Series(nav.to_numpy(), index=dates).dropna().sort_index()
    close = close[~close.index.isna()]
    close = close[~close.index.duplicated(keep="last")]
    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=1860)
    close = close.loc[close.index >= cutoff]
    if close.empty or float(close.iloc[-1]) <= 0:
        raise ValueError(f"No usable NAV history for scheme {code}.")
    name = meta.get("scheme_name") or code
    return {
        "ticker": code, "name": name, "asset_class": "Mutual fund",
        "sector": meta.get("scheme_category") or "Mutual fund",
        "currency": "INR", "close": close,
        "volume": pd.Series(dtype=float),
        "source": "MFapi.in / AMFI", "as_of": close.index[-1].date().isoformat(),
    }


def fetch_usd_inr() -> pd.Series:
    rates = yf.Ticker("USDINR=X").history(period="5y", interval="1d", auto_adjust=True)
    if rates is None or rates.empty:
        raise ValueError("USD/INR FX feed is unavailable; cannot value USD holdings in INR.")
    result = _series(rates["Close"])
    if result.empty:
        raise ValueError("No usable USD/INR FX history.")
    return result


def price_in_inr(asset: dict, usd_inr: pd.Series | None = None) -> pd.Series:
    close = asset["close"]
    if asset["currency"] == "INR":
        return close
    if usd_inr is None or usd_inr.empty:
        raise ValueError("USD/INR conversion data is required for US stocks.")
    rate = usd_inr.reindex(close.index, method="ffill", tolerance=pd.Timedelta(days=7))
    converted = (close * rate).dropna()
    if converted.empty:
        raise ValueError("No overlapping USD/INR exchange-rate history.")
    return converted


def normalize_holdings(frame: pd.DataFrame) -> list[dict]:
    """Support the provided Ticker | Quantity | Avg Buy Price CSV convention."""
    if frame is None or frame.empty:
        return []
    aliases = {
        "ticker": "Ticker", "symbol": "Ticker",
        "scheme code": "Ticker", "scheme": "Ticker",
        "ticker / scheme code": "Ticker",
        "quantity": "Quantity", "units": "Quantity",
        "avg buy price": "Avg Buy Price", "average buy price": "Avg Buy Price",
        "type": "Type", "asset type": "Type",
    }
    normalized = frame.rename(columns={
        c: aliases.get(str(c).strip().casefold(), str(c)) for c in frame.columns
    }).copy()
    missing = {"Ticker", "Quantity"} - set(normalized.columns)
    if missing:
        raise ValueError("Upload must contain Ticker and Quantity (Avg Buy Price is optional).")
    if "Type" not in normalized:
        normalized["Type"] = "Stock"
    if "Avg Buy Price" not in normalized:
        normalized["Avg Buy Price"] = 0.0
    rows = []
    for _, row in normalized.iterrows():
        code = str(row["Ticker"]).strip()
        if not code or code.lower() in {"nan", "none"}:
            continue
        kind = str(row["Type"]).strip().lower()
        asset_type = "Mutual fund" if kind in {"mf", "mutual fund", "fund"} else "Stock"
        quantity = pd.to_numeric(row["Quantity"], errors="coerce")
        raw_basis = str(row["Avg Buy Price"]).strip()
        basis = 0.0 if raw_basis.lower() in {"", "nan", "none"} else parse_inr(raw_basis)
        if pd.isna(quantity) or quantity <= 0:
            raise ValueError(f"Quantity for {code} must be greater than zero.")
        rows.append({"Type": asset_type, "Ticker": code,
                     "Quantity": float(quantity),
                     "Avg Buy Price": float(basis)})
    if len(rows) > 12:
        raise ValueError("Use at most 12 holdings per analysis to respect free-data providers.")
    # Combine exact duplicate identifiers; unit-price remains a weighted average.
    combined = {}
    for row in rows:
        key = (row["Type"], row["Ticker"].upper())
        if key not in combined:
            combined[key] = row.copy()
        else:
            item = combined[key]
            new_quantity = item["Quantity"] + row["Quantity"]
            item["Avg Buy Price"] = (
                item["Avg Buy Price"] * item["Quantity"] +
                row["Avg Buy Price"] * row["Quantity"]
            ) / new_quantity
            item["Quantity"] = new_quantity
    return list(combined.values())


def resolve_portfolio(holdings: list[dict], stock_loader, fund_loader, fx_loader) -> tuple[list[dict], list[str]]:
    positions, errors = [], []
    fx = None
    for item in holdings:
        symbol = item["Ticker"]
        try:
            asset = fund_loader(symbol) if item["Type"] == "Mutual fund" else stock_loader(symbol)
            if asset["currency"] == "USD" and fx is None:
                fx = fx_loader()
            history_inr = price_in_inr(asset, fx)
            as_of = pd.Timestamp(history_inr.index[-1])
            if pd.Timestamp.now().normalize() - as_of > pd.Timedelta(days=12):
                raise ValueError("Last quote / NAV is more than 12 days old.")
            quantity = float(item["Quantity"])
            latest = float(history_inr.iloc[-1])
            record = dict(asset)
            record.update({
                "quantity": quantity, "avg_buy_price": item.get("Avg Buy Price", 0),
                "history_inr": history_inr,
                "latest_inr": latest,
                "value_inr": quantity * latest,
            })
            positions.append(record)
        except Exception as exc:
            errors.append(f"{symbol}: {exc}")
    return positions, errors


def fetch_stock_batch(symbols: list[str]) -> tuple[list[dict], list[str]]:
    """Batch candidate snapshots in one Yahoo Finance request.

    Missing symbols are skipped with explicit errors; market prices are never
    fabricated. This is a curated INR/US universe, not arbitrary FX guessing.
    """
    unique = list(dict.fromkeys(str(symbol).strip().upper() for symbol in symbols))
    if not unique:
        return [], []
    # An ampersand is valid in Yahoo Finance symbols such as M&M.NS.
    # Reject individual malformed candidates rather than crashing the
    # entire recommendation page because of one bad symbol.
    pattern = re.compile(r"[A-Z0-9.&\-]{1,24}")
    valid = [symbol for symbol in unique if pattern.fullmatch(symbol)]
    errors = [f"{symbol!r}: skipped invalid stock ticker" for symbol in unique
              if not pattern.fullmatch(symbol)]
    if not valid:
        return [], errors or ["No valid candidate tickers."]
    if len(valid) > 55:
        errors.append(f"Candidate universe capped at 55 symbols; {len(valid) - 55} not requested.")
        valid = valid[:55]
    try:
        frame = yf.download(
            tickers=valid, period="5y", interval="1d", auto_adjust=True,
            group_by="ticker", threads=True, progress=False,
        )
    except Exception as exc:
        return [], errors + [f"Batch quote download failed: {exc}"]
    if frame is None or frame.empty:
        return [], errors + ["Market data provider returned no candidate quotes."]
    out = []
    for symbol in valid:
        try:
            if isinstance(frame.columns, pd.MultiIndex):
                block = frame[symbol] if symbol in frame.columns.get_level_values(0) else frame.xs(symbol, axis=1, level=1)
            else:
                block = frame
            if "Close" not in block or "Volume" not in block:
                raise ValueError("Missing close/volume from provider")
            close = _series(block["Close"])
            vol = _series(block["Volume"])
            if len(close) < 61 or close.iloc[-1] <= 0:
                raise ValueError("Insufficient observed close history")
            if pd.Timestamp.now().normalize() - close.index[-1] > pd.Timedelta(days=12):
                raise ValueError("Last close more than 12 days old")
            out.append({
                "ticker": symbol, "name": symbol, "asset_class": "Stock",
                "sector": STOCK_SECTORS.get(symbol, "Unclassified"),
                "currency": "INR" if symbol.endswith((".NS", ".BO")) else "USD",
                "close": close, "volume": vol, "source": "Yahoo Finance",
                "as_of": close.index[-1].date().isoformat(),
            })
        except Exception as exc:
            errors.append(f"{symbol}: {exc}")
    return out, errors
