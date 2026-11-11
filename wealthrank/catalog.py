"""Curated sector navigation; NOT a complete exchange listing.

Every row needs an obtainable quote at runtime. Sector classifications here are
application categories (not licensed industry-taxonomy assignments).
"""
from __future__ import annotations

MARKET_SECTORS: dict[str, dict[str, tuple[str, ...]]] = {
    "India": {
        "Technology": (
            "INFY.NS","TCS.NS","HCLTECH.NS","WIPRO.NS","TECHM.NS",
            "PERSISTENT.NS","COFORGE.NS","LTIM.NS","MPHASIS.NS",
            "OFSS.NS","KPITTECH.NS","BSOFT.NS","CYIENT.NS",
        ),
        "Financials": (
            "HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS",
            "KOTAKBANK.NS","BAJFINANCE.NS","BAJAJFINSV.NS",
            "INDUSINDBK.NS","HDFCLIFE.NS","SBILIFE.NS",
            "CHOLAFIN.NS","ICICIPRULI.NS","FEDERALBNK.NS",
        ),
        "Consumer": (
            "ITC.NS","HINDUNILVR.NS","TITAN.NS","NESTLEIND.NS",
            "DABUR.NS","BRITANNIA.NS","ASIANPAINT.NS","GODREJCP.NS",
            "TATACONSUM.NS","MARICO.NS","COLPAL.NS","TRENT.NS",
            "PIDILITIND.NS",
        ),
        "Healthcare": (
            "SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","APOLLOHOSP.NS",
            "DIVISLAB.NS","LUPIN.NS","AUROPHARMA.NS","BIOCON.NS",
            "TORNTPHARM.NS","ALKEM.NS","SYNGENE.NS","GLENMARK.NS",
        ),
        "Industrials": (
            "LT.NS","SIEMENS.NS","BEL.NS","HAL.NS","BHEL.NS",
            "ABB.NS","BEML.NS","CUMMINSIND.NS","ADANIPORTS.NS",
            "CONCOR.NS","THERMAX.NS","POLYCAB.NS",
        ),
        "Energy": (
            "RELIANCE.NS","ONGC.NS","COALINDIA.NS","BPCL.NS",
            "IOC.NS","HINDPETRO.NS","OIL.NS","GAIL.NS",
            "PETRONET.NS","MGL.NS","IGL.NS","GUJGASLTD.NS",
        ),
        "Utilities": (
            "NTPC.NS","POWERGRID.NS","TATAPOWER.NS","JSWENERGY.NS",
            "ADANIPOWER.NS","TORNTPOWER.NS","NHPC.NS","SJVN.NS",
            "CESC.NS","NLCINDIA.NS","INOXWIND.NS",
        ),
        "Automotive": (
            "MARUTI.NS","M&M.NS","EICHERMOT.NS","BAJAJ-AUTO.NS",
            "HEROMOTOCO.NS","TVSMOTOR.NS","TATAMOTORS.NS",
            "ASHOKLEY.NS","MOTHERSON.NS","BOSCHLTD.NS","EXIDEIND.NS",
        ),
        "Materials": (
            "ULTRACEMCO.NS","JSWSTEEL.NS","TATASTEEL.NS",
            "HINDALCO.NS","GRASIM.NS","SHREECEM.NS","AMBUJACEM.NS",
            "ACC.NS","JINDALSTEL.NS","VEDL.NS","SAIL.NS",
        ),
    },
    "US": {
        "Technology": (
            "AAPL","MSFT","NVDA","GOOGL","META","AMD","INTC","ORCL",
            "CRM","ADBE","AVGO","CSCO","NOW","IBM","PLTR","PANW",
            "IONQ","QBTS","RGTI","QUBT",
        ),
        "Financials": (
            "JPM","BAC","WFC","C","GS","MS","V","MA","AXP",
            "BLK","SCHW","PNC","USB",
        ),
        "Consumer": (
            "AMZN","TSLA","NFLX","WMT","COST","HD","LOW","MCD",
            "NKE","SBUX","TGT","PEP","KO","PG","DIS",
        ),
        "Healthcare": (
            "JNJ","UNH","ABBV","PFE","MRK","LLY","AMGN",
            "GILD","ABT","BMY","TMO","ISRG",
        ),
        "Industrials": (
            "GE","CAT","HON","DE","UPS","FDX","EMR","ETN",
            "MMM","PH","ITW","ROK",
        ),
        "Energy": (
            "XOM","CVX","COP","SLB","EOG","OXY","PSX",
            "MPC","VLO","KMI","WMB",
        ),
        "Aerospace & Defense": (
            "SPCX","RKLB","BA","LMT","RTX","NOC","GD",
            "HII","LHX","TDG","HEI","KTOS",
        ),
    },
}

def sectors_for_market(market: str) -> list[str]:
    if market not in MARKET_SECTORS:
        raise ValueError("Market must be India or US.")
    return list(MARKET_SECTORS[market])


def tickers_for_sector(market: str, sector: str) -> tuple[str, ...]:
    try:
        return MARKET_SECTORS[market][sector]
    except KeyError as exc:
        raise ValueError(f"Unknown category {sector!r} for {market!r}.") from exc


def sector_map() -> dict[str, str]:
    result: dict[str, str] = {}
    for markets in MARKET_SECTORS.values():
        for sector, tickers in markets.items():
            for ticker in tickers:
                if ticker in result and result[ticker] != sector:
                    raise ValueError(f"Ambiguous sector classification for {ticker}")
                result[ticker] = sector
    return result
