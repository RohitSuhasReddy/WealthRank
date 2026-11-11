"""Dedicated, navigable WealthRank screens.

No screen renders another screen below it. Portfolio data is kept in session
state by the root app and reused in analytics / discovery / FIRE.
"""
from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from wealthrank.analytics import period_returns
from wealthrank.charts import performance_chart
from wealthrank.navigation import navigate
from wealthrank.catalog import sectors_for_market, tickers_for_sector
from wealthrank.category_ranking import rank_sector_stocks
from wealthrank.stock_metrics import instrument_metrics
from wealthrank.theme import metrics, note, recommendation_card


def _pct(number: float | None) -> str:
    return "—" if number is None else f"{number:+.1%}"


def _unsigned(number: float | None) -> str:
    return "—" if number is None else f"{number:.1%}"


def _decimal(number: float | None) -> str:
    return "—" if number is None else f"{number:.2f}"


def _market(asset: dict) -> str:
    return "India" if asset["currency"] == "INR" else "US"


def _benchmark(asset: dict, benchmark_loader) -> tuple[pd.Series | None, str, float]:
    market = _market(asset)
    ticker, riskfree = ("^NSEI", .06) if market == "India" else ("^GSPC", .04)
    try:
        return benchmark_loader(ticker), ticker, riskfree
    except Exception as exc:
        st.caption(f"Benchmark {ticker} unavailable ({exc}); alpha and beta are hidden.")
        return None, ticker, riskfree


def _stock_snapshot(asset: dict, benchmark: pd.Series | None, riskfree: float) -> dict:
    return instrument_metrics(asset["close"], benchmark, riskfree)


def _metric_row(values: dict, instrument: dict, benchmark_ticker: str, riskfree: float) -> None:
    metrics([
        ("1-YEAR RETURN", _pct(values["return_1y"]), "Observed price / NAV"),
        ("ALPHA / JENSEN", _pct(values["alpha"]), f"Annualised vs {benchmark_ticker}"),
        ("BETA", _decimal(values["beta"]), f"Daily returns vs {benchmark_ticker}"),
        ("SHARPE RATIO", _decimal(values["sharpe"]), f"Risk-free assumption {riskfree:.0%}"),
    ])
    metrics([
        ("5-YEAR CAGR", _pct(values["cagr_5y"]), "Only if near-5y history exists"),
        ("ANNUAL VOLATILITY", _unsigned(values["annual_volatility"]), "Daily × √252"),
        ("MAX DRAWDOWN", _pct(values["max_drawdown"]), "Trailing ~12 months"),
        ("OBSERVATIONS", str(values["observations"]), "Daily risk returns"),
    ])


def stock_analytics(positions: list[dict], benchmark_loader) -> None:
    """Dedicated holdings screen with stock-level performance and CAPM metrics."""
    if not positions:
        note("No live holdings yet. Open Portfolio, enter tickers / AMFI codes and click Analyse my portfolio.")
        st.button("Open Portfolio →", on_click=navigate, args=("portfolio",), key="analytics_to_portfolio",
                  type="primary")
        return
    selection = {p["ticker"]: p for p in positions}
    portfolio_table = []
    benchmark_cache = {}
    for asset in positions:
        market = _market(asset)
        ticker, rf = ("^NSEI", .06) if market == "India" else ("^GSPC", .04)
        if ticker not in benchmark_cache:
            try:
                benchmark_cache[ticker] = benchmark_loader(ticker)
            except Exception:
                benchmark_cache[ticker] = None
        m = _stock_snapshot(asset, benchmark_cache[ticker], rf)
        portfolio_table.append({
            "Asset": asset["ticker"], "Type": asset["asset_class"],
            "Sector/category": asset["sector"],
            "1Y return": _pct(m["return_1y"]),
            "Alpha": _pct(m["alpha"]), "Beta": _decimal(m["beta"]),
            "Sharpe": _decimal(m["sharpe"]), "Volatility": _unsigned(m["annual_volatility"]),
            "As of": asset["as_of"],
        })

    st.markdown('<div class="wr-miniheading">YOUR HOLDINGS / ANALYTICAL SCORECARD</div>',
                unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(portfolio_table), hide_index=True, use_container_width=True)
    st.caption("Metrics are computed from observed history. For Indian holdings the proxy "
               "benchmark is NIFTY 50; US equities use S&P 500. Mutual-fund benchmarks "
               "may differ from their category-specific benchmarks.")

    col_a, col_b = st.columns([1.6, 1], gap="large")
    with col_a:
        selected = st.selectbox(
            "Inspect a holding", list(selection.keys()),
            format_func=lambda ticker: selection[ticker]["name"],
        )
    with col_b:
        period = st.radio("Chart range", ["1W", "1M", "6M", "1Y", "5Y"], horizontal=True, index=3)
    asset = selection[selected]
    benchmark, benchmark_ticker, riskfree = _benchmark(asset, benchmark_loader)
    analysis = _stock_snapshot(asset, benchmark, riskfree)
    st.markdown(f'<div class="wr-miniheading">{asset["ticker"]} / STOCK INTELLIGENCE</div>',
                unsafe_allow_html=True)
    _metric_row(analysis, asset, benchmark_ticker, riskfree)
    with st.container(border=True):
        st.markdown('<div class="wr-panel-head">Observed price / NAV performance</div>',
                    unsafe_allow_html=True)
        view = st.radio(
            "Vertical scale", ["Zoomed price", "Percentage change"],
            horizontal=True, key="holding_chart_scale",
            help="Zoomed price uses the observed low/high; percentage change rebases the first price to 0%.",
        )
        try:
            st.plotly_chart(
                performance_chart(asset, period, view=view),
                use_container_width=True,
                key=f"holding_chart_{selected}_{period}_{view}",
            )
        except ValueError as exc:
            st.info(str(exc))
    returns = period_returns(asset["close"])
    st.dataframe(pd.DataFrame([
        {
            "Horizon": horizon,
            "Price-only return": _pct(stat["absolute"]) if stat else "Not enough history",
            "Annualised": _pct(stat["annualized"])
            if stat and stat["annualized"] is not None else "—",
        }
        for horizon, stat in returns.items()
    ]), hide_index=True, use_container_width=True)
    note("Jensen alpha is an annualised historical CAPM residual, not an expectation "
         "of future outperformance. Sharpe assumes an annual risk-free rate of 6% "
         "for INR instruments / 4% for USD instruments. Dividends, taxes and fees "
         "are excluded from price-only returns. Unavailable values are shown as —.")


def ranked_discovery(
    positions: list[dict],
    risk: str,
    preferred_sectors: list[str],
    candidate_loader,
    benchmark_loader,
) -> None:
    """Sector-specific top-ten ranking, independent of having a portfolio."""
    india_value = sum(p["value_inr"] for p in positions if p.get("currency") == "INR")
    total_value = sum(p["value_inr"] for p in positions)
    default_market = 0 if not total_value or india_value >= total_value / 2 else 1

    market_col, sector_col, label_col = st.columns([.9, 1.4, 1], gap="large")
    with market_col:
        market = st.selectbox("Stock market", ["India", "US"], index=default_market,
                              key="sector_market")
    with sector_col:
        sector = st.selectbox("Stock category / sector", sectors_for_market(market),
                              key="sector_category")
    with label_col:
        st.markdown('<div class="wr-miniheading">CATEGORY LEADERBOARD</div>',
                    unsafe_allow_html=True)
        st.caption(f"Top 10 observed stocks · {risk} risk preference")

    symbols = tickers_for_sector(market, sector)
    matching = {sym.upper() for sym in symbols}
    owned_here = [
        p for p in positions
        if p.get("asset_class") == "Stock"
        and str(p.get("ticker", "")).upper() in matching
    ]
    # User holdings are displayed even if the free-data provider is offline.
    if owned_here:
        cards = []
        for holding in owned_here:
            label = html.escape(str(holding.get("ticker", "Stock")))
            units = float(holding.get("quantity", 0))
            market_value = float(holding.get("value_inr", 0))
            cards.append(
                '<div class="wr-owned-item">'
                f'<strong>{label}</strong><span>ALREADY OWNED</span>'
                f'<small>{units:,.4f} units · ₹{market_value:,.0f} value</small>'
                '</div>'
            )
        st.markdown(
            '<div class="wr-owned-wrap"><div class="wr-owned-heading">'
            '● ALREADY IN YOUR PORTFOLIO · ' + html.escape(sector) + '</div>'
            + ''.join(cards) + '</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "These stocks are highlighted separately and excluded from new-stock rankings. "
            "You can still inspect their charts in the deep-dive section."
        )
    else:
        st.caption(f"No verified holdings in {sector} yet.")

    st.caption(f"Screening {len(symbols)} curated {market} {sector} candidates. "
               "Selecting another category immediately recalculates its own ranking.")
    refresh = st.button("↻ Refresh current category", key="refresh_category")
    key = (market, sector)
    if refresh or st.session_state.get("sector_loaded_key") != key:
        with st.spinner(f"Loading {sector} stock prices…"):
            try:
                assets, errors = candidate_loader(tuple(symbols))
            except Exception as exc:
                assets, errors = [], [str(exc)]
            st.session_state["sector_loaded_key"] = key
            st.session_state["sector_assets"] = assets
            st.session_state["sector_errors"] = errors

    assets = st.session_state.get("sector_assets", [])
    errors = st.session_state.get("sector_errors", [])
    if not assets:
        note("No usable live stock data was received for this category. "
             "Try again later or choose a different sector; rankings are never fabricated.")
        with st.expander("Source errors", expanded=True):
            for error in errors:
                st.caption(error)
        return

    ranked, skipped = rank_sector_stocks(
        portfolio=positions, candidates=assets,
        sector=sector, risk_preference=risk, limit=10,
    )
    st.session_state["recommendations"] = ranked
    flags_count = sum(bool(r["flags"]) for r in ranked)
    metrics([
        ("MARKET", market, "Exchange-listed equities"),
        ("CATEGORY", sector, "Sector-specific list"),
        ("RANKED STOCKS", f"{len(ranked)} / 10", "Observed stock histories only"),
        ("RISK FLAGS", str(flags_count), "Visible, not silently removed"),
    ])
    st.caption(
        "Each category has its own ranking. The algorithm ranks using observed volatility, "
        "history length, a recent-return component, and liquidity screening. "
        "High-risk stocks remain visible with flags for comparison. "
        "Ranks are NOT expected returns, financial advice, or a guarantee of suitability."
    )
    benchmark_symbol = "^NSEI" if market == "India" else "^GSPC"
    rf = .06 if market == "India" else .04
    try:
        benchmark = benchmark_loader(benchmark_symbol)
    except Exception as exc:
        benchmark = None
        st.caption(f"Benchmark temporarily unavailable: {exc}. Alpha and beta shown as —.")

    lookup = {asset["ticker"]: asset for asset in assets}
    owned_lookup = {asset["ticker"]: asset for asset in owned_here}
    table = []
    for rank, item in enumerate(ranked, 1):
        details = _stock_snapshot(lookup[item["ticker"]], benchmark, rf)
        table.append({
            "Rank": rank,
            "Stock": item["ticker"],
            "Category": sector,
            "Score / 100": item["score"],
            "1Y return": _pct(details["return_1y"]),
            "Alpha": _pct(details["alpha"]),
            "Beta": _decimal(details["beta"]),
            "Sharpe": _decimal(details["sharpe"]),
            "Volatility": _unsigned(details["annual_volatility"]),
            "Risk note": " · ".join(item["flags"]) if item["flags"] else "Within screening bands",
        })
    if not table:
        st.info("No stocks in this category have enough measured history to rank.")
    else:
        st.markdown('<div class="wr-miniheading">SECTOR TOP TEN / LIVE MEASURED DATA</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            pd.DataFrame(table), hide_index=True, use_container_width=True,
            column_config={"Score / 100": st.column_config.ProgressColumn(
                "Score / 100", min_value=0, max_value=100, format="%.1f"
            )},
        )
        by_rank = {row["Stock"]: row["Rank"] for row in table}
        detail_tickers = list(by_rank) + [
            ticker for ticker in owned_lookup if ticker not in by_rank
        ]
        chosen = st.selectbox(
            "Stock deep-dive", detail_tickers,
            key=f"ranked_detail_{market}_{sector}",
            format_func=lambda symbol: (
                f"✓ ALREADY OWNED · {symbol}" if symbol in owned_lookup
                else f"#{by_rank[symbol]} · {symbol}"
            ),
        )
        if chosen in owned_lookup:
            asset = owned_lookup[chosen]
            st.markdown(
                '<div class="wr-owned-selection">✓ ALREADY OWNED · '
                + html.escape(chosen)
                + ' — held in your portfolio, not ranked as a new stock idea.</div>',
                unsafe_allow_html=True,
            )
        else:
            asset = lookup[chosen]
            entry = next(item for item in ranked if item["ticker"] == chosen)
            recommendation_card(entry, by_rank[chosen])
            if entry["flags"]:
                st.warning("Risk considerations: " + " · ".join(entry["flags"]))
        detail = _stock_snapshot(asset, benchmark, rf)
        _metric_row(detail, asset, benchmark_symbol, rf)
        timeline, scaling = st.columns([1.25, 1], gap="medium")
        with timeline:
            period = st.radio("Price-history window", ["1W", "1M", "6M", "1Y", "5Y"],
                              index=3, horizontal=True)
        with scaling:
            view = st.radio("Chart scale", ["Zoomed price", "Percentage change"],
                            horizontal=True, key="category_chart_scale")
        with st.container(border=True):
            try:
                st.plotly_chart(
                    performance_chart(asset, period, view=view),
                    use_container_width=True,
                    key=f"category_chart_{chosen}_{period}_{view}",
                )
            except ValueError as exc:
                st.info(str(exc))

    with st.expander("Universe, scoring, and unavailable tickers", expanded=False):
        st.write(
            f"The {market} / {sector} category starts with {len(symbols)} "
            "curated tickers. Stocks already owned are highlighted separately; "
            "unavailable quotes or fewer than 60+ returns cannot be ranked. "
            "When fewer than ten have usable "
            "data, the screen reports the actual available count rather than inventing entries."
        )
        st.write(
            "Score components: 61% risk-volatility fit, 17% liquidity, "
            "12% observed history length, 10% bounded recent price return; "
            "penalties are applied to risk-band breaches, illiquidity, and "
            "portfolio concentration. This is a transparent, illustrative "
            "screening formula, not a proven predictive model."
        )
        for problem in [*skipped, *errors]:
            st.caption(problem)
    note("Market prices may be delayed or inaccessible. Historical alpha, beta, "
         "Sharpe and returns are descriptive statistics and never guaranteed forecasts.")
