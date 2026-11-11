"""Dedicated, navigable WealthRank screens.

No screen renders another screen below it. Portfolio data is kept in session
state by the root app and reused in analytics / discovery / FIRE.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from wealthrank.analytics import period_returns
from wealthrank.charts import performance_chart
from wealthrank.navigation import navigate
from wealthrank.recommendations import candidate_universe, rank_candidates
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
        try:
            st.plotly_chart(performance_chart(asset, period), use_container_width=True,
                            key=f"holding_chart_{selected}_{period}")
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
    """Top 10 guarded stock ideas, metrics table and selected stock deep-dive."""
    if not positions:
        note("Portfolio context is required for personalised ranking. Add at least one verified holding first.")
        st.button("Set up Portfolio →", on_click=navigate, args=("portfolio",),
                  type="primary", key="discover_to_portfolio")
        return

    india_value = sum(p["value_inr"] for p in positions if p["currency"] == "INR")
    overall = sum(p["value_inr"] for p in positions)
    initial = 0 if india_value >= overall / 2 else 1
    first, second, third = st.columns([1, 1.2, 1], gap="large")
    with first:
        market = st.selectbox("Recommendation market", ["India", "US"], index=initial)
    with second:
        mode = st.radio("Ranking strategy", ["Similar", "Diversifying"], horizontal=True)
    with third:
        st.markdown('<div class="wr-miniheading">CURRENT PROFILE</div>', unsafe_allow_html=True)
        st.caption(f"{risk} risk · up to 10 eligible stock matches")

    if st.button("Rank 10 stock ideas ↗", type="primary", use_container_width=True,
                 key="load_discovery"):
        universe = candidate_universe("INR" if market == "India" else "USD")
        held = {a["ticker"].upper() for a in positions}
        symbols = tuple(symbol for symbol in universe if symbol not in held)
        with st.status("Fetching stock histories and applying risk guardrails…", expanded=True) as status:
            assets, errors = candidate_loader(symbols)
            st.session_state["ranked_candidate_assets"] = assets
            st.session_state["ranked_candidate_errors"] = errors
            st.session_state["ranked_candidate_market"] = market
            st.write(f"Retrieved {len(assets)} observed histories out of {len(symbols)} candidates.")
            status.update(label="Candidate batch loaded", state="complete", expanded=False)

    if st.session_state.get("ranked_candidate_market") != market:
        note("Click Rank 10 stock ideas to load this market. No fabricated or fallback recommendations appear.")
        return
    assets = st.session_state.get("ranked_candidate_assets", [])
    if not assets:
        st.info("No usable candidate prices returned. Check network access and try again.")
        for message in st.session_state.get("ranked_candidate_errors", []):
            st.caption(message)
        return

    ranked, excluded = rank_candidates(
        portfolio=positions, candidates=assets, risk_preference=risk,
        mode=mode, limit=10, preferred_sectors=preferred_sectors,
    )
    st.session_state["recommendations"] = ranked
    metrics([
        ("CANDIDATES OBSERVED", str(len(assets)), f"Curated {market} stock universe"),
        ("RANKED MATCHES", f"{len(ranked)} / 10", "Only passing all guardrails"),
        ("SCREENED OUT", str(len(excluded)), "Risk, concentration, liquidity"),
        ("RANKING STYLE", mode, f"{risk} risk preference"),
    ])
    st.caption("Rank is an explainable relevance score, not expected performance. "
               "If fewer than ten stocks pass the filters, fewer than ten are shown.")

    benchmark_ticker = "^NSEI" if market == "India" else "^GSPC"
    rf = .06 if market == "India" else .04
    try:
        benchmark = benchmark_loader(benchmark_ticker)
    except Exception as exc:
        benchmark = None
        st.warning(f"Benchmark unavailable: {exc}. Alpha and beta cannot be calculated.")

    by_symbol = {a["ticker"]: a for a in assets}
    table = []
    for i, item in enumerate(ranked, start=1):
        details = _stock_snapshot(by_symbol[item["ticker"]], benchmark, rf)
        table.append({
            "Rank": i, "Ticker": item["ticker"], "Sector": item["sector"],
            "Score /100": round(item["score"], 1),
            "1Y return": _pct(details["return_1y"]),
            "Alpha": _pct(details["alpha"]), "Beta": _decimal(details["beta"]),
            "Volatility": _unsigned(details["annual_volatility"]),
            "Sharpe": _decimal(details["sharpe"]),
            "Why selected": item["explanation"],
        })

    st.markdown('<div class="wr-miniheading">TOP STOCK IDEAS / RANKING & METRICS</div>',
                unsafe_allow_html=True)
    if table:
        st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True,
                     column_config={"Score /100": st.column_config.ProgressColumn(
                         "Score /100", min_value=0, max_value=100, format="%.1f",
                     )})
        selected = st.selectbox(
            "Inspect a recommended stock",
            [row["Ticker"] for row in table],
            format_func=lambda code: f"{next(row['Rank'] for row in table if row['Ticker'] == code):02d} · {code}",
        )
        item = next(r for r in ranked if r["ticker"] == selected)
        recommendation_card(item, next(i for i, r in enumerate(ranked, start=1) if r["ticker"] == selected))
        details = _stock_snapshot(by_symbol[selected], benchmark, rf)
        _metric_row(details, by_symbol[selected], benchmark_ticker, rf)
        period = st.radio("Price-history window", ["1W", "1M", "6M", "1Y", "5Y"],
                          index=3, horizontal=True)
        with st.container(border=True):
            try:
                st.plotly_chart(
                    performance_chart(by_symbol[selected], period),
                    use_container_width=True, key=f"idea_chart_{selected}_{period}",
                )
            except ValueError as exc:
                st.info(str(exc))
    else:
        note("No stocks passed the chosen risk profile and sector cap. "
             "This is a valid screened result, not a fetch failure. "
             "You can adjust your portfolio risk preference.")

    with st.expander("Methodology, data failures and guardrail exclusions", expanded=False):
        st.write("Curated liquid equity universe (not exhaustive). Scores use risk fit, "
                 "exposure similarity/diversification, optional preferred sectors and "
                 "concentration. Stocks must pass historical volatility and estimated "
                 "median traded-value screens; a hypothetical 10% position is tested "
                 "against a 45% sector-exposure limit.")
        if excluded:
            st.write("Screened out:")
            for issue in excluded:
                st.caption(issue)
        for issue in st.session_state.get("ranked_candidate_errors", []):
            st.caption(f"Market-data error: {issue}")
    note("Market data from Yahoo Finance may be delayed. Alpha, beta, Sharpe and "
         "historical returns are descriptive statistics, not forecasts or investment advice.")
