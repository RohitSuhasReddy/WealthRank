"""WealthRank — a finance-first, animated Streamlit application.

Run with: streamlit run app.py
Data displayed as market observations comes only from free public providers.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import io

import pandas as pd
import streamlit as st

from wealthrank.analytics import allocation, period_returns, risk_metrics
from wealthrank.charts import (
    allocation_donut, comparison_chart, evaluation_chart,
    fire_projection_chart, performance_chart,
)
from wealthrank.data import (
    STOCK_SECTORS, fetch_fund, fetch_stock, fetch_usd_inr,
    normalize_holdings, price_in_inr, resolve_portfolio, search_funds,
)
from wealthrank.evaluation import run_synthetic_lab
from wealthrank.fire import FireInputs, fire_target_today, project_fire, real_return, retirement_snapshot
from wealthrank.recommendations import (
    FUND_QUERIES, candidate_universe, rank_candidates, select_fund_search_result,
)
from wealthrank.theme import footer, hero, inject_css, metrics, note, recommendation_card, section


st.set_page_config(
    page_title="WealthRank — Finance, made human",
    page_icon="◉", layout="wide", initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_stock(ticker: str) -> dict:
    return fetch_stock(ticker)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cached_fund(code: str) -> dict:
    return fetch_fund(code)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fx() -> pd.Series:
    return fetch_usd_inr()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_fund_search(query: str) -> list[dict]:
    return search_funds(query)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_benchmark(ticker: str, usd_converted: bool = False) -> pd.Series:
    data = cached_stock(ticker)
    if usd_converted:
        return price_in_inr(data, cached_fx())
    return data["close"]


def currency(amount: float | None, compact: bool = True) -> str:
    if amount is None:
        return "—"
    if compact and abs(amount) >= 10_000_000:
        return f"₹{amount / 10_000_000:,.2f} Cr"
    if compact and abs(amount) >= 100_000:
        return f"₹{amount / 100_000:,.2f} L"
    return f"₹{amount:,.0f}"


def percent(value: float | None, signed: bool = False) -> str:
    if value is None:
        return "—"
    return f"{value:+.1%}" if signed else f"{value:.1%}"


def default_holdings() -> pd.DataFrame:
    # Example *quantities* only. Prices and analytics are never mocked.
    return pd.DataFrame([
        {"Type": "Stock", "Ticker": "RELIANCE.NS", "Quantity": 6.0, "Avg Buy Price": 0.0},
        {"Type": "Stock", "Ticker": "INFY.NS", "Quantity": 8.0, "Avg Buy Price": 0.0},
        {"Type": "Stock", "Ticker": "ICICIBANK.NS", "Quantity": 5.0, "Avg Buy Price": 0.0},
    ])


def upload_data(upload) -> pd.DataFrame:
    raw = upload.getvalue()
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("Uploaded portfolio exceeds 10 MB.")
    if upload.name.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw))
    return pd.read_excel(io.BytesIO(raw))


def display_portfolio() -> tuple[list[dict], str, list[str]]:
    section(
        "portfolio", "01", "GET STARTED", "Your holdings.<br><em>In focus.</em>",
        "Import a portfolio or edit the starter holdings. Every displayed market value is fetched from public data.",
    )
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        st.markdown('<div class="wr-miniheading">THE PORTFOLIO EDITOR</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Import CSV / Excel (Ticker, Quantity, Avg Buy Price; optional Type)",
            type=["csv", "xlsx"], help="Set Type to Mutual fund and Ticker to the AMFI scheme code for mutual funds.",
        )
        try:
            starter = upload_data(uploaded) if uploaded else default_holdings()
            normalized = normalize_holdings(starter)
            edit_frame = pd.DataFrame(normalized, columns=["Type", "Ticker", "Quantity", "Avg Buy Price"])
            unique_key = hashlib.sha256(uploaded.getvalue()).hexdigest()[:12] if uploaded else "starter"
            editor = st.data_editor(
                edit_frame, num_rows="dynamic", hide_index=True, use_container_width=True,
                key=f"editor_{unique_key}",
                column_config={
                    "Type": st.column_config.SelectboxColumn("Type", options=["Stock", "Mutual fund"], required=True),
                    "Ticker": st.column_config.TextColumn("Ticker / AMFI code", help="e.g. INFY.NS or 125497"),
                    "Quantity": st.column_config.NumberColumn("Units", min_value=0.00001, step=1.0, format="%.4f"),
                    "Avg Buy Price": st.column_config.NumberColumn("Avg buy price (optional)", min_value=0.0, format="%.2f"),
                },
            )
        except Exception as exc:
            st.error(f"Unable to parse portfolio: {exc}")
            editor = pd.DataFrame()
    with right:
        st.markdown('<div class="wr-miniheading">PERSONALISE YOUR VIEW</div>', unsafe_allow_html=True)
        risk = st.selectbox("Your risk preference", ["Moderate", "Conservative", "Aggressive"])
        preferred_sectors = st.multiselect("Preferred sectors (optional)", sorted(set(STOCK_SECTORS.values())))
        note("Stock tickers use Yahoo Finance codes (for example, INFY.NS or AAPL). "
             "Mutual funds use an AMFI scheme code to avoid mixing direct, regular or IDCW plans.")
        st.download_button(
            "↓ Download CSV template", data=default_holdings().to_csv(index=False),
            file_name="wealthrank_portfolio_template.csv", mime="text/csv",
            use_container_width=True,
        )

    run = st.button("Analyse my portfolio  ↗", type="primary", use_container_width=True)
    if run:
        try:
            holdings = normalize_holdings(editor)
            if not holdings:
                st.warning("Enter at least one holding with a positive quantity.")
            else:
                with st.status("Fetching verified prices and NAVs…", expanded=True) as status:
                    st.write("Reading stocks from Yahoo Finance and funds from MFapi.in.")
                    positions, errors = resolve_portfolio(
                        holdings, cached_stock, cached_fund, cached_fx
                    )
                    st.session_state["positions"] = positions
                    st.session_state["portfolio_errors"] = errors
                    st.session_state["recommendations"] = []
                    st.session_state["recommendation_assets"] = []
                    status.update(label="Portfolio refresh complete", state="complete", expanded=False)
        except Exception as exc:
            st.error(f"Please correct the portfolio inputs: {exc}")
    return st.session_state.get("positions", []), risk, preferred_sectors


def display_analytics(positions: list[dict]) -> None:
    section(
        "analytics", "02", "THE BIG PICTURE", "Less noise.<br><em>More signal.</em>",
        "Allocation, volatility, benchmark beta and concentration — computed from actual available price histories.",
    )
    if not positions:
        note("No verified portfolio snapshot yet. Click 'Analyse my portfolio' above. "
             "The FIRE planner below works without a portfolio.")
        return

    table = allocation(positions)
    main_inr = sum(p["value_inr"] for p in positions if p["currency"] == "INR")
    use_india = main_inr >= sum(p["value_inr"] for p in positions) / 2
    benchmark_symbol = "^NSEI" if use_india else "^GSPC"
    benchmark = None
    try:
        benchmark = cached_benchmark(benchmark_symbol, usd_converted=not use_india)
    except Exception as exc:
        st.caption(f"Benchmark feed unavailable ({benchmark_symbol}): {exc}")
    stats = risk_metrics(positions, benchmark)
    score = stats["risk_score"]
    risk_label = ("—" if score is None else
                  "Lower" if score < 33 else "Moderate" if score < 66 else "Elevated")
    metrics([
        ("VERIFIED PORTFOLIO VALUE", currency(stats["total"]), f"{len(positions)} priced holdings · INR equivalent"),
        ("ANNUALISED VOLATILITY", percent(stats["volatility"]), f"{stats['observations']} aligned return observations"),
        ("MAX CONCENTRATION", percent(stats["concentration"]), "Largest holding by market value"),
        ("RELATIVE RISK SCORE", "—" if score is None else f"{score} / 100", f"Rule-based · {risk_label}"),
    ])

    left, right = st.columns([1.05, .95], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Allocation / by holding</div>', unsafe_allow_html=True)
            st.plotly_chart(allocation_donut(table), use_container_width=True, key="allocation_chart")
    with right:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Risk and exposures</div>', unsafe_allow_html=True)
            st.metric("Approximate benchmark beta", f'{stats["beta"]:.2f}' if stats["beta"] is not None else "—")
            st.caption(f"Benchmark: {benchmark_symbol}. Calculated using overlapping INR-denominated daily returns.")
            sector = table.groupby("Sector")["Weight"].sum().sort_values(ascending=False)
            st.markdown('<div class="wr-miniheading">SECTOR / CATEGORY WEIGHTS</div>', unsafe_allow_html=True)
            for name, weight in sector.items():
                st.write(f"{name}  ·  {weight:.1%}")
                st.progress(min(float(weight), 1.0))
            st.caption("Risk score is a relative heuristic, not a certified rating or loss forecast.")

    holdings_table = pd.DataFrame([{
        "Holding": p["name"], "Type": p["asset_class"],
        "Units": p["quantity"], "Last price / NAV (INR)": p["latest_inr"],
        "Position value (INR)": p["value_inr"], "As of": p["as_of"],
    } for p in positions])
    with st.expander("Show verified holding-level valuations", expanded=False):
        st.dataframe(holdings_table, hide_index=True, use_container_width=True)
        st.caption("US quotes are converted into INR using observed USD/INR rates. "
                   "Market prices may be delayed; no real-time execution guarantee.")
    for warning in stats["warnings"]:
        st.caption(f"⚠ {warning}")
    for message in st.session_state.get("portfolio_errors", []):
        st.warning(message)


def load_candidate_assets(positions: list[dict]) -> tuple[list[dict], list[str]]:
    currency_weight = {
        c: sum(p["value_inr"] for p in positions if p["currency"] == c)
        for c in ("INR", "USD")
    }
    preferred_currency = max(currency_weight, key=currency_weight.get)
    held = {p["ticker"].upper() for p in positions}
    symbols = [s for s in candidate_universe(preferred_currency) if s not in held][:8]
    candidates = []
    problems = []
    fx = None
    for ticker in symbols:
        try:
            asset = cached_stock(ticker)
            if asset["currency"] == "USD" and fx is None:
                fx = cached_fx()
            record = dict(asset)
            record["history_inr"] = price_in_inr(asset, fx)
            candidates.append(record)
        except Exception as exc:
            problems.append(f"{ticker}: {exc}")
    if preferred_currency == "INR":
        for query in FUND_QUERIES:
            try:
                matching = cached_fund_search(query)
                code = select_fund_search_result(matching)
                if not code or code in held:
                    continue
                asset = cached_fund(code)
                record = dict(asset)
                record["history_inr"] = price_in_inr(asset)
                candidates.append(record)
            except Exception as exc:
                problems.append(f"{query}: {exc}")
    return candidates, problems


def display_recommendations(positions: list[dict], risk: str, preferred_sectors: list[str]) -> None:
    section(
        "discover", "03", "THE DISCOVERY ENGINE", "Find your<br><em>next perspective.</em>",
        "Ranked ideas, similarity and diversification, transparent scores, and filters that can reject unsuitable candidates.",
    )
    if not positions:
        note("Analyse a portfolio to activate the live recommendation engine.")
        return
    c1, c2, c3 = st.columns([1, 1, 1], gap="medium")
    with c1:
        mode = st.radio("Recommendation style", ["Diversifying", "Similar"], horizontal=True)
    with c2:
        limit = st.select_slider("Ideas to show", options=[3, 4, 5], value=5)
    with c3:
        st.markdown('<div class="wr-miniheading">DATA-BASED UNIVERSE</div>', unsafe_allow_html=True)
        st.caption("Curated liquid-equity shortlist + selected Indian MF plans. Not the entire market.")

    if st.button("Discover matches  ↗", type="primary", use_container_width=True):
        with st.status("Screening the candidate universe…", expanded=True) as status:
            candidates, problems = load_candidate_assets(positions)
            st.write(f"Evaluated {len(candidates)} candidates with obtainable data.")
            st.session_state["recommendation_assets"] = candidates
            st.session_state["candidate_errors"] = problems
            status.update(label="Screening finished", state="complete", expanded=False)

    candidates = st.session_state.get("recommendation_assets", [])
    if candidates:
        ranked, rejected = rank_candidates(
            positions, candidates, risk, mode, limit=limit,
            preferred_sectors=preferred_sectors,
        )
        st.session_state["recommendations"] = ranked
        metrics([
            ("CANDIDATES WITH DATA", str(len(candidates)), "Public stocks + fund NAVs"),
            ("PASSED GUARDRAILS", str(len(ranked)), f"Top {limit} eligible matches"),
            ("SCREENED OUT", str(len(rejected)), "Volatility · liquidity · sector"),
            ("STYLE", mode, f"{risk} risk preference"),
        ])
        for index, item in enumerate(ranked, start=1):
            recommendation_card(item, index)
        if not ranked:
            note("No candidate passed this risk/guardrail configuration. "
                 "Try a different risk band or inspect the reasons below.")
        with st.expander("How scoring works / exclusions", expanded=False):
            st.write("Ranking combines risk-volatility fit, sector/category relevance, "
                     "and existing exposure. A proposed 10% position is screened against "
                     "a 45% sector/category concentration cap.")
            st.write("Stocks require an estimated 20-day median traded-value threshold. "
                     "Mutual-fund redemption liquidity cannot be inferred from NAV data "
                     "and must be checked separately.")
            if rejected:
                st.write("Guardrail exclusions:", *rejected)
            for err in st.session_state.get("candidate_errors", []):
                st.caption(f"Data unavailable: {err}")
        st.caption("Scores are relevance heuristics, not return forecasts, buy ratings, "
                   "or suitability assessments. Funds may have exit loads or lock-ins.")
    else:
        note("Click 'Discover matches' to fetch and filter live candidates. "
             "The app does not display placeholder recommendation scores.")


def display_performance(positions: list[dict]) -> None:
    section(
        "performance", "04", "TIME IN CONTEXT", "The story<br><em>behind the line.</em>",
        "Observed price/NAV series, switchable horizons, chart zoom and hover-level detail.",
    )
    assets = positions + st.session_state.get("recommendation_assets", [])
    unique_assets = {a["ticker"]: a for a in assets}
    if not unique_assets:
        note("Verified price histories will appear here after you analyse holdings.")
        return
    left, right = st.columns([1.4, 1], gap="large")
    with left:
        selected = st.selectbox(
            "Instrument", options=list(unique_assets.keys()),
            format_func=lambda k: unique_assets[k]["name"],
        )
    with right:
        period = st.radio("Timeframe", ["1W", "1M", "6M", "1Y", "5Y"], index=3, horizontal=True)
    asset = unique_assets[selected]
    c1, c2, c3 = st.columns(3)
    c1.metric("Latest observed quote / NAV",
              f"{'₹' if asset['currency'] == 'INR' else '$'}{float(asset['close'].iloc[-1]):,.2f}")
    c2.metric("Source", asset["source"])
    c3.metric("As of", asset["as_of"])
    with st.container(border=True):
        try:
            st.plotly_chart(performance_chart(asset, period), use_container_width=True,
                            key=f"price_{selected}_{period}")
        except ValueError as exc:
            st.info(str(exc))
    summary = period_returns(asset["close"])
    table = pd.DataFrame([{
        "Period": name,
        "Observed return": percent(value["absolute"], signed=True) if value else "Insufficient history",
        "Annualised": percent(value["annualized"], signed=True) if value and value["annualized"] is not None else "—",
    } for name, value in summary.items()])
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.caption("Price-only returns exclude dividends, trading fees and taxes. "
               "NAV history is historical; past performance does not predict future returns.")


def display_fire(positions: list[dict]) -> None:
    section(
        "fire", "05", "FINANCIAL INDEPENDENCE", "Make the future<br><em>feel tangible.</em>",
        "Model net worth, the inflation-adjusted retirement target and the purchasing power of your savings.",
    )
    portfolio_value = sum(p["value_inr"] for p in positions)
    with st.container(border=True):
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown('<div class="wr-miniheading">LIFE & SPENDING</div>', unsafe_allow_html=True)
            age = st.slider("Current age", min_value=18, max_value=80, value=29)
            retire_age = st.slider("Target retirement age", min_value=age + 1, max_value=100,
                                   value=min(100, max(55, age + 15)))
            expenses = st.number_input("Current monthly expenses (₹)", min_value=0.0,
                                       max_value=50_000_000.0, value=65_000.0, step=5_000.0)
            withdrawal = st.slider("Assumed annual withdrawal rate (%)", 2.0, 6.0, 4.0, .25)
        with right:
            st.markdown('<div class="wr-miniheading">CAPITAL & ASSUMPTIONS</div>', unsafe_allow_html=True)
            use_portfolio = st.checkbox("Use analysed portfolio as starting net worth",
                                        value=bool(portfolio_value > 0), disabled=not bool(portfolio_value))
            initial_value = portfolio_value if use_portfolio else 2_500_000.0
            wealth = st.number_input("Starting net worth (₹)", min_value=0.0,
                                     max_value=5_000_000_000.0, value=float(initial_value),
                                     step=100_000.0, disabled=use_portfolio)
            sip = st.number_input("Monthly investment / SIP (₹)", min_value=0.0,
                                  max_value=50_000_000.0, value=25_000.0, step=5_000.0)
            nominal = st.slider("Expected nominal annual return (%)", -10.0, 25.0, 10.0, .5)
            inflation = st.slider("Expected annual inflation (%)", 0.0, 15.0, 6.0, .5)
            step_up = st.slider("Annual SIP increase (%)", 0.0, 20.0, 0.0, 1.0)

    assumptions = FireInputs(
        current_age=age, monthly_expenses=expenses, net_worth=wealth,
        annual_return=nominal / 100, inflation=inflation / 100,
        monthly_sip=sip, withdrawal_rate=withdrawal / 100,
        sip_step_up=step_up / 100,
    )
    try:
        projection, years_to_fire = project_fire(assumptions, years=100 - age)
        retiring = retirement_snapshot(projection, retire_age)
        target_now = fire_target_today(assumptions)
    except ValueError as exc:
        st.error(f"Cannot calculate FIRE scenario: {exc}")
        return
    fire_year = "Not by age 100" if years_to_fire is None else (
        "Already reached" if years_to_fire == 0 else f"{years_to_fire:.1f} yrs"
    )
    metrics([
        ("FIRE TARGET TODAY", currency(target_now), "Current annual spending ÷ withdrawal rate"),
        ("NET WORTH AT TARGET AGE", currency(retiring["Net worth"]), f"Nominal · age {retire_age}"),
        ("VALUE IN TODAY'S RUPEES", currency(retiring["Today's rupees"]), "Deflated by projected inflation"),
        ("TIME TO FIRE", fire_year, "Monthly crossing · if target is reached"),
    ])
    st.markdown('<div class="wr-panel-head">Net worth projection / nominal, real & FIRE threshold</div>',
                unsafe_allow_html=True)
    with st.container(border=True):
        st.plotly_chart(fire_projection_chart(projection, retire_age),
                        use_container_width=True, key="fire_growth")
    projected_target = retiring["FIRE target"]
    difference = retiring["Net worth"] - projected_target
    if difference >= 0:
        st.success(f"At age {retire_age}, your modelled corpus exceeds the inflation-adjusted "
                   f"target by {currency(difference)}.")
    else:
        st.warning(f"At age {retire_age}, the modelled corpus is {currency(abs(difference))} "
                   "below the projected FIRE target.")
    st.caption(f"Implied REAL annual return: {real_return(assumptions.annual_return, assumptions.inflation):.2%}. "
               "Return is a constant assumption, not a forecast; actual returns and withdrawal outcomes vary.")

    st.markdown('<div class="wr-miniheading">WHAT-IF SCENARIOS</div>', unsafe_allow_html=True)
    what_if = st.radio(
        "Explore a change", ["Increase monthly SIP by 20%", "Reduce monthly expenses by 10%"],
        horizontal=True,
    )
    adjusted = (
        replace(assumptions, monthly_sip=sip * 1.2)
        if what_if.startswith("Increase")
        else replace(assumptions, monthly_expenses=expenses * .9)
    )
    new_projection, new_time = project_fire(adjusted, years=100 - age)
    with st.container(border=True):
        st.plotly_chart(
            comparison_chart(projection, new_projection, "Base plan", what_if),
            use_container_width=True, key="fire_sensitivity",
        )
    time_string = "not reached by age 100" if new_time is None else f"{new_time:.1f} years"
    st.caption(f"Scenario crosses the FIRE threshold in {time_string}. "
               "Reducing expenses changes the FIRE target, not the net-worth line.")
    with st.expander("Calculation method and assumptions", expanded=False):
        st.markdown(
            "Monthly compounding uses \\(r_m=(1+r_{annual})^{1/12}-1\\) with SIP contributions "
            "at month-end. The FIRE threshold grows with projected spending inflation; "
            "real net worth discounts the nominal balance back to today's rupees."
        )
        st.latex(r"\mathrm{FIRE\ target}_{t}=\frac{12\cdot\mathrm{monthly\ expenses}\cdot(1+\pi)^t}{\mathrm{withdrawal\ rate}}")
        st.markdown("Withdrawal rates are planning assumptions, not guaranteed safe outcomes. "
                    "Taxes, investment costs, sequence risk and changing spending are not modelled.")


def display_lab() -> None:
    section(
        "lab", "06", "MODEL EVALUATION", "Measure the<br><em>thinking.</em>",
        "An offline sandbox for ranking quality, feature ablation and an explicitly simulated A/B comparison.",
    )
    experiment = run_synthetic_lab()
    ndcg = experiment["ndcg"]
    precision = experiment["precision"]
    metrics([
        ("SYNTHETIC USER PROFILES", str(experiment["profiles"]), "Deterministic · seed 42"),
        ("BASELINE NDCG@5", f"{ndcg['Sector only']:.1%}", "Sector-only ranker"),
        ("HYBRID NDCG@5", f"{ndcg['Hybrid']:.1%}", "Risk + sector + liquidity"),
        ("SIMULATED CTR LIFT", percent(experiment["relative_lift"], signed=True), "Proxy clicks, NOT user data"),
    ])
    left, right = st.columns([1.4, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Feature ablation / offline NDCG</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(evaluation_chart(ndcg), use_container_width=True, key="ablation")
    with right:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Ranking methods / top-5 quality</div>',
                        unsafe_allow_html=True)
            st.dataframe(pd.DataFrame([{
                "Method": method, "NDCG@5": round(ndcg[method], 3),
                "Precision@5": round(precision[method], 3),
            } for method in ndcg]), hide_index=True, use_container_width=True)
            st.caption("The relevance labels are synthetic proxies generated from "
                       "risk/sector preferences — not external relevance judgments.")
    note("A/B simulation draws illustrative clicks from proxy relevance probabilities. "
         "Lift is a mock experiment statistic, NOT a measured product result. "
         "Use real opt-in feedback and unbiased evaluation before claiming model improvements.")


def main() -> None:
    inject_css()
    hero()
    positions, risk, preferred_sectors = display_portfolio()
    display_analytics(positions)
    display_recommendations(positions, risk, preferred_sectors)
    display_performance(positions)
    display_fire(positions)
    display_lab()
    footer()


if __name__ == "__main__":
    main()
