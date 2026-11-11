"""Whole-net-worth view: verified investment holdings + entered asset/debt estimates."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from wealthrank.charts import allocation_donut
from wealthrank.money import format_inr, parse_inr
from wealthrank.theme import metrics, note


def net_worth_breakdown(positions: list[dict]) -> None:
    st.markdown('<div class="wr-miniheading">COMPLETE NET WORTH / BALANCE SHEET</div>',
                unsafe_allow_html=True)
    st.caption("Investment prices come from public feeds. Bank balances, savings, property "
               "and debt are user-entered estimates; no personal bank account is connected.")
    fields = [
        ("cash", "Cash and bank balances", "1,00,000"),
        ("deposits", "Deposits and other savings", "0"),
        ("other_assets", "Other assets / property", "0"),
        ("liabilities", "Loans and liabilities", "0"),
    ]
    inputs = {}
    columns = st.columns(4, gap="small")
    for column, (field, label, default) in zip(columns, fields):
        with column:
            prior = st.session_state.get("saved_nw_" + field)
            value = format_inr(prior) if prior is not None else default
            inputs[field] = st.text_input(
                label + " (₹)", value=value, key="nw_input_" + field,
                help="Indian comma grouping supported, e.g. 25,00,000",
            )
    try:
        amounts = {key: parse_inr(raw) for key, raw in inputs.items()}
    except ValueError as exc:
        st.error(f"Check the net-worth amounts: {exc}")
        return
    for key, amount in amounts.items():
        st.session_state["saved_nw_" + key] = amount
    invested = sum(a["value_inr"] for a in positions)
    gross = invested + amounts["cash"] + amounts["deposits"] + amounts["other_assets"]
    networth = gross - amounts["liabilities"]
    st.session_state["net_worth_total"] = networth
    st.session_state["invested_portfolio_total"] = invested

    def amount_string(value: float) -> str:
        return ("−" if value < 0 else "") + "₹" + format_inr(abs(value))
    metrics([
        ("TOTAL NET WORTH", amount_string(networth), "Gross assets minus debt"),
        ("GROSS ASSETS", amount_string(gross), "Investments + other assets"),
        ("LOANS / LIABILITIES", amount_string(amounts["liabilities"]), "User-entered obligations"),
        ("INVESTMENTS", amount_string(invested), f"{len(positions)} priced instruments"),
    ])
    categories = pd.DataFrame([
        {"Asset": "Portfolio holdings", "Value": invested},
        {"Asset": "Cash / bank", "Value": amounts["cash"]},
        {"Asset": "Deposits / savings", "Value": amounts["deposits"]},
        {"Asset": "Other assets", "Value": amounts["other_assets"]},
    ])
    categories = categories.loc[categories["Value"] > 0]
    left, right = st.columns([1.1, .9], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Asset mix / before liabilities</div>',
                        unsafe_allow_html=True)
            if not categories.empty:
                st.plotly_chart(allocation_donut(categories), use_container_width=True,
                                key="networth_allocation")
            else:
                st.info("Enter positive assets to view their allocation.")
    with right:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Where you stand</div>',
                        unsafe_allow_html=True)
            st.metric("Debt as a share of assets", f"{amounts['liabilities']/gross:.1%}" if gross else "—")
            st.metric("Estimated non-portfolio assets", amount_string(gross - invested))
            st.metric("Market-valued investments", amount_string(invested))
            st.caption("The chart excludes liabilities and cannot validate manually entered values.")
    if not positions:
        note("To add stocks or mutual funds to this snapshot, use the portfolio editor above "
             "and run Analyse my portfolio.")
