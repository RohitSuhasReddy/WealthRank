"""User-editable FIRE planner: exact entry or sliders; clear retirement spending.

The return is a user assumption and future spending preserves today's real
lifestyle unless the user explicitly changes current spending.
"""
from __future__ import annotations

from dataclasses import replace

import streamlit as st

from wealthrank.charts import comparison_chart, fire_projection_chart
from wealthrank.fire import (
    FireInputs, fire_target_today, first_year_withdrawal,
    project_fire, real_return, retirement_expenses, retirement_snapshot,
)
from wealthrank.money import format_inr, parse_inr
from wealthrank.theme import metrics, note, section


def _money(value: float, compact: bool = False) -> str:
    if compact and abs(value) >= 10_000_000:
        return f"₹{value / 10_000_000:,.2f} Cr"
    if compact and abs(value) >= 100_000:
        return f"₹{value / 100_000:,.2f} L"
    return ("−" if value < 0 else "") + "₹" + format_inr(abs(value))


def _parameter(
    label: str, name: str, minimum: int | float, maximum: int | float,
    default: int | float, step: int | float = 1,
    help_text: str | None = None,
) -> int | float:
    """Provide both slider and precise-number modes with retained shared values."""
    base = "fire_canonical_" + name
    if base not in st.session_state:
        st.session_state[base] = default
    st.session_state[base] = min(max(st.session_state[base], minimum), maximum)
    typed = st.session_state.get("fire_control_mode", "Type exact values") == "Type exact values"
    key = f"fire_control_{name}_{'typed' if typed else 'slider'}"
    if key not in st.session_state or st.session_state[key] != st.session_state[base]:
        st.session_state[key] = st.session_state[base]

    def copy_value() -> None:
        st.session_state[base] = st.session_state[key]

    settings = dict(
        label=label, min_value=minimum, max_value=maximum,
        step=step, key=key, on_change=copy_value, help=help_text,
    )
    if typed:
        return st.number_input(**settings)
    return st.slider(**settings)


def _selected_capital(positions: list[dict]) -> float | None:
    components: dict[str, float] = st.session_state.get("networth_components") or {}
    if not components:
        st.info("Open Portfolio → Net Worth to enter asset categories before choosing a custom mix.")
        return None
    default = [name for name in components if name != "Property / other assets"
               and components[name] > 0]
    selected = st.multiselect(
        "Assets to include in FIRE capital", list(components),
        default=default, key="fire_selected_assets",
        help="Usually include liquid/investible balances, not the value of your residence.",
    )
    deduct = st.checkbox(
        "Subtract outstanding debt from this capital",
        value=True, key="fire_custom_debt",
    )
    debt = float(st.session_state.get("networth_liabilities") or 0)
    capital = sum(float(components[name]) for name in selected) - (debt if deduct else 0)
    st.caption(f"Selected asset total: {_money(sum(components[name] for name in selected))}. "
               f"Debt adjustment: {_money(debt) if deduct else 'none'}.")
    return capital


def render_fire(positions: list[dict]) -> None:
    section(
        "fire", "04", "FINANCIAL INDEPENDENCE", "Your future.<br><em>On your terms.</em>",
        "Enter exact numbers or use sliders. Spending at retirement automatically reflects "
        "the same lifestyle after inflation.",
    )
    portfolio_value = sum(float(p["value_inr"]) for p in positions)
    saved_total = st.session_state.get("net_worth_total")

    st.radio(
        "How would you like to adjust the assumptions?",
        ["Type exact values", "Quick sliders"], horizontal=True,
        key="fire_control_mode",
    )
    capital_choices = ["Enter manually"]
    if positions:
        capital_choices.append("Investment portfolio")
    if saved_total is not None:
        capital_choices.append("Total net worth")
    if st.session_state.get("networth_components"):
        capital_choices.append("Choose my assets")
    choice = st.radio(
        "Starting capital", capital_choices, horizontal=True,
        key="fire_capital_source",
        help="You can enter an independent starting amount, use your holdings, "
             "or select a subset of your net-worth assets.",
    )

    with st.container(border=True):
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown('<div class="wr-miniheading">YOUR LIFESTYLE</div>', unsafe_allow_html=True)
            age = int(_parameter("Current age", "age", 18, 80, 29))
            target_age = int(_parameter(
                "Retirement age", "retire_age", age + 1, 100, max(55, age + 1),
            ))
            expense_text = st.text_input(
                "Monthly expenses today (₹)", "65,000", key="fire_expenses_new",
                help="Use Indian commas (e.g. 65,000 or 1,25,000).",
            )
            withdrawal = float(_parameter(
                "Annual withdrawal rate (%)", "withdrawal", 1.5, 8.0, 4.0, .25,
                "Percentage of retirement corpus withdrawn in the FIRST retirement year. "
                "This does not determine inflation or change your expense assumption.",
            ))
        with right:
            st.markdown('<div class="wr-miniheading">YOUR INVESTMENTS</div>', unsafe_allow_html=True)
            capital = None
            if choice == "Enter manually":
                principal_text = st.text_input(
                    "Starting investable net worth (₹)", "25,00,000",
                    key="fire_principal_new",
                    help="Type an exact figure with or without Indian commas.",
                )
            elif choice == "Investment portfolio":
                capital = portfolio_value
                st.metric("Verified investment value", _money(capital))
            elif choice == "Total net worth":
                capital = float(saved_total)
                st.metric("Full net worth", _money(capital))
                st.caption("Property and other assets may be illiquid. Consider choosing specific "
                           "assets rather than assuming they can all compound as investments.")
            else:
                capital = _selected_capital(positions)
            sip_text = st.text_input(
                "Monthly SIP / investment (₹)", "25,000", key="fire_sip_new",
                help="Enter exactly, e.g. 25,000.",
            )
            annual_return = float(_parameter(
                "Nominal annual investment return (%)", "return", -10.0, 25.0, 10.0, .25,
                "Hypothetical nominal compounded annual return, not a guaranteed forecast.",
            ))
            inflation = float(_parameter(
                "Annual expense inflation (%)", "inflation", 0.0, 15.0, 6.0, .25,
                "Expenses at retirement = today's spending × (1 + inflation)^years.",
            ))
            step_up = float(_parameter(
                "Annual SIP increase (%)", "step_up", 0.0, 20.0, 0.0, .5,
            ))

    try:
        current_expenses = parse_inr(expense_text)
        monthly_sip = parse_inr(sip_text)
        if choice == "Enter manually":
            capital = parse_inr(principal_text)
        if capital is None:
            return
        if capital < 0:
            st.error("Starting investable capital is negative. Choose other assets or enter a "
                     "non-negative starting amount; the FIRE investment model cannot compound debt.")
            return
        params = FireInputs(
            current_age=age, monthly_expenses=current_expenses,
            net_worth=float(capital), monthly_sip=monthly_sip,
            annual_return=annual_return / 100, inflation=inflation / 100,
            withdrawal_rate=withdrawal / 100, sip_step_up=step_up / 100,
        )
        trajectory, crossing = project_fire(params, years=100 - age)
        retiring = retirement_snapshot(trajectory, target_age)
        future_spending = retirement_expenses(params, target_age)
    except ValueError as exc:
        st.error(f"Please correct the financial inputs: {exc}")
        return

    st.markdown('<div class="wr-miniheading">YOUR EXPECTED EXPENSES AT RETIREMENT</div>',
                unsafe_allow_html=True)
    metrics([
        ("MONTHLY SPENDING TODAY", _money(current_expenses, compact=True), "Your stated lifestyle"),
        ("MONTHLY AT RETIREMENT", _money(future_spending["monthly"], compact=True),
         f"At age {target_age} · {inflation:g}% yearly inflation"),
        ("YEARLY AT RETIREMENT", _money(future_spending["annual"], compact=True),
         "12 × inflation-adjusted monthly spending"),
        ("FIRE CORPUS REQUIRED", _money(future_spending["corpus"], compact=True),
         f"Future annual spending ÷ {withdrawal:g}%"),
    ])
    st.caption(
        f"Exact retirement spending at age {target_age}: "
        f"{_money(future_spending['monthly'])} per month / {_money(future_spending['annual'])} per year. "
        f"Assumes your lifestyle remains the same in today's purchasing power for "
        f"{target_age - age} years."
    )
    with st.expander("What does annual withdrawal rate mean?", expanded=True):
        st.markdown(
            f"**It is not the rate your expenses grow.** You set inflation separately at "
            f"**{inflation:g}%**. Withdrawal rate is a way to estimate the investment corpus "
            f"needed to fund retirement. At **{withdrawal:g}%**, the initial annual withdrawal "
            f"is {withdrawal:g}% of your retirement corpus. For your assumed expenses, "
            f"the required corpus at age **{target_age}** is "
            f"**{_money(future_spending['corpus'])}**: "
            f"**{_money(future_spending['annual'])} ÷ {withdrawal / 100:.4f}**. "
            "A 4% rate is a common planning heuristic, not a guaranteed safe withdrawal "
            "rate; taxes, fees, market sequence risk and retirement duration matter."
        )

    fire_time = ("Not reached by age 100" if crossing is None
                 else "Already reached" if crossing == 0
                 else f"{crossing:.1f} years")
    initial_budget = first_year_withdrawal(retiring["Net worth"], params.withdrawal_rate)
    metrics([
        ("PROJECTED CORPUS", _money(retiring["Net worth"], compact=True),
         f"Nominal at age {target_age}"),
        ("VALUE IN TODAY'S ₹", _money(retiring["Today's rupees"], compact=True),
         "Inflation discounted"),
        ("YEARLY WITHDRAWAL BUDGET", _money(initial_budget, compact=True),
         f"{withdrawal:g}% of projected corpus"),
        ("ESTIMATED TIME TO FIRE", fire_time, "Monthly crossing against rising target"),
    ])
    st.caption(
        f"Your projected corpus could initially support about "
        f"{_money(initial_budget / 12)} per month under the chosen withdrawal rule, "
        f"versus the retirement spending goal of {_money(future_spending['monthly'])} per month."
    )

    horizon = st.radio(
        "Projection chart horizon",
        ["Retirement + 10 years", "Full projection to age 100"],
        horizontal=True, key="fire_chart_horizon",
        help="Focus the default chart around retirement so growth early in life is not flattened by large future values.",
    )
    chart_data = (trajectory.loc[trajectory["Age"] <= min(100, target_age + 10)]
                  if horizon.startswith("Retirement") else trajectory)
    with st.container(border=True):
        st.markdown('<div class="wr-panel-head">Net-worth and inflation-adjusted FIRE threshold</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fire_projection_chart(chart_data, target_age),
                        use_container_width=True,
                        key=f"fire_growth_{horizon}")
    gap = retiring["Net worth"] - future_spending["corpus"]
    if gap >= 0:
        st.success(
            f"At age {target_age}, the projected corpus is {_money(gap)} above the "
            "inflation-adjusted FIRE target."
        )
    else:
        st.warning(
            f"At age {target_age}, the projected corpus falls {_money(abs(gap))} short "
            "of your retirement-spending target."
        )
    st.caption(
        f"Implied real annual return: {real_return(params.annual_return, params.inflation):.2%}. "
        "Your return and inflation inputs are scenarios, not predictions."
    )

    st.markdown('<div class="wr-miniheading">SCENARIO COMPARISON</div>',
                unsafe_allow_html=True)
    scenario = st.radio(
        "What would you like to change?",
        ["Increase SIP by 20%", "Reduce current spending by 10%"], horizontal=True,
        key="fire_scenario",
    )
    modified = (
        replace(params, monthly_sip=monthly_sip * 1.2)
        if scenario.startswith("Increase") else
        replace(params, monthly_expenses=current_expenses * .9)
    )
    alternate, new_crossing = project_fire(modified, years=100 - age)
    with st.container(border=True):
        st.plotly_chart(
            comparison_chart(trajectory, alternate, "Original plan", scenario),
            use_container_width=True, key="fire_sensitivity",
        )
    result = "not reached by age 100" if new_crossing is None else f"{new_crossing:.1f} years"
    st.caption(f"Alternative FIRE crossing: {result}. Spending reductions change the "
               "FIRE target, not the investment-growth line.")
    with st.expander("Calculation assumptions", expanded=False):
        st.latex(
            r"\mathrm{Expenses}_{ret} = \mathrm{Expenses}_{today}(1+\pi)^{years}"
        )
        st.latex(
            r"\mathrm{FIRE\ corpus}_{ret} = \frac{12\times\mathrm{Monthly\ expenses}_{ret}}{\mathrm{withdrawal\ rate}}"
        )
        st.markdown(
            "Investments compound monthly at a constant nominal expected rate. SIPs are "
            "added at month-end and may step up each year. The model omits taxes, fees, "
            "changes in salary/spending, and market-return uncertainty."
        )
