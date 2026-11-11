"""Editable net worth: direct entry or selected, independently controlled components."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from wealthrank.charts import allocation_donut
from wealthrank.money import format_inr, parse_inr, parse_signed_inr
from wealthrank.theme import metrics, note


def _money(value: float) -> str:
    return ("−" if value < 0 else "") + "₹" + format_inr(abs(value))


def net_worth_breakdown(positions: list[dict]) -> None:
    st.markdown('<div class="wr-miniheading">YOUR NET WORTH / BUILD IT YOUR WAY</div>',
                unsafe_allow_html=True)
    st.caption(
        "Use a single net-worth number or a detailed balance sheet. "
        "The investment valuation uses real observed prices; other amounts are your own estimates."
    )
    mode = st.radio(
        "How would you like to enter net worth?",
        ["Add assets and liabilities", "Enter one total directly"],
        key="networth_method", horizontal=True,
    )
    invested = sum(float(asset["value_inr"]) for asset in positions)

    if mode == "Enter one total directly":
        custom = st.text_input(
            "Your total net worth (₹)",
            value=st.session_state.get("networth_single_text", "0"),
            help="Can be positive or negative; example: 25,00,000 or -2,50,000.",
            key="nw_total_manual",
        )
        try:
            net = parse_signed_inr(custom)
        except ValueError as exc:
            st.error(f"Enter a valid net-worth amount: {exc}")
            st.session_state.pop("net_worth_total", None)
            return
        st.session_state["networth_single_text"] = custom
        st.session_state["net_worth_total"] = net
        st.session_state["networth_components"] = {"Entered net worth": net}
        st.session_state["networth_liabilities"] = 0.0
        metrics([
            ("NET WORTH", _money(net), "Your manually entered total"),
            ("PRICED HOLDINGS (REFERENCE)", _money(invested), f"{len(positions)} market-valued investments"),
        ])
        note("The direct total replaces the asset-by-asset calculation; it is NOT added to "
             "your holdings, preventing accidental double counting. "
             "In FIRE, you can still use only your investment portfolio instead.")
        return

    include_portfolio = st.checkbox(
        "Include my verified stock / mutual-fund portfolio in net worth",
        value=True, key="nw_include_portfolio",
        help="Uncheck this to calculate a completely manual balance sheet.",
    )
    fields = [
        ("cash", "Cash and bank balances", "0"),
        ("deposits", "FDs / other deposits", "0"),
        ("investments", "Other investments (not above)", "0"),
        ("property", "Property / other assets", "0"),
        ("debt", "Outstanding loans / debt", "0"),
    ]
    entries = {}
    cols = st.columns([1, 1, 1], gap="small")
    for index, (slug, label, default) in enumerate(fields):
        with cols[index % 3]:
            entries[slug] = st.text_input(
                label + " (₹)", value=st.session_state.get("nw_last_" + slug, default),
                key="nw_component_" + slug,
                help="Enter 25,00,000 or 2,500,000; use a positive amount for debt.",
            )
    try:
        values = {name: parse_inr(text) for name, text in entries.items()}
    except ValueError as exc:
        st.error(f"Check your entered assets or debt: {exc}")
        st.session_state.pop("net_worth_total", None)
        return
    for slug, text in entries.items():
        st.session_state["nw_last_" + slug] = text

    components = {
        "Verified portfolio": invested if include_portfolio else 0.0,
        "Cash / bank": values["cash"],
        "Deposits": values["deposits"],
        "Other investments": values["investments"],
        "Property / other assets": values["property"],
    }
    gross = sum(components.values())
    debt = values["debt"]
    net = gross - debt
    st.session_state["net_worth_total"] = net
    st.session_state["networth_components"] = components
    st.session_state["networth_liabilities"] = debt

    metrics([
        ("TOTAL NET WORTH", _money(net), "Assets − loans and debt"),
        ("TOTAL ASSETS", _money(gross), "Selected assets before debt"),
        ("TOTAL LIABILITIES", _money(debt), "Your entered outstanding debt"),
        ("VERIFIED INVESTMENTS", _money(invested), "Not added when excluded above"),
    ])
    table = pd.DataFrame([{"Asset": label, "Value": amount}
                          for label, amount in components.items() if amount > 0])
    left, right = st.columns([1.1, .9], gap="large")
    with left:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Asset allocation / before debt</div>', unsafe_allow_html=True)
            if not table.empty:
                st.plotly_chart(allocation_donut(table), use_container_width=True,
                                key="networth_mix")
            else:
                st.info("Add an asset amount to see your allocation.")
    with right:
        with st.container(border=True):
            st.markdown('<div class="wr-panel-head">Net-worth composition</div>', unsafe_allow_html=True)
            st.metric("Debt / gross assets", f"{debt / gross:.1%}" if gross else "—")
            st.metric("Assets excluding property", _money(gross - values["property"]))
            st.metric("Market-valued portfolio", _money(invested))
            st.caption("Property values and other manual balances are not market verified.")
    if not positions:
        note("Portfolio holdings have not been analysed yet. "
             "The figure currently consists only of your manually entered values.")
