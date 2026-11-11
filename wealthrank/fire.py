"""Monthly-compounding, inflation-aware FIRE calculations.

Returns are nominal; inflation is applied once to future expenses and to the
purchasing-power chart. Contributions arrive at the END of each month.
All amounts are INR; the caller is responsible for currency conversion.
"""
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FireInputs:
    current_age: int
    monthly_expenses: float
    net_worth: float
    annual_return: float  # decimal nominal rate (e.g. 0.10)
    inflation: float  # decimal (e.g. 0.06)
    monthly_sip: float
    withdrawal_rate: float = 0.04
    sip_step_up: float = 0.0  # annual contribution increase


def validate_fire(inputs: FireInputs) -> None:
    if not 18 <= inputs.current_age < 100:
        raise ValueError("Current age must be between 18 and 99.")
    if min(inputs.monthly_expenses, inputs.net_worth, inputs.monthly_sip) < 0:
        raise ValueError("Expenses, wealth, and SIP must not be negative.")
    if not -1 < inputs.annual_return <= 1:
        raise ValueError("Expected annual return must be above -100% and at most 100%.")
    if not -1 < inputs.inflation <= 1:
        raise ValueError("Inflation must be above -100% and at most 100%.")
    if not 0 < inputs.withdrawal_rate <= 1:
        raise ValueError("Withdrawal rate must be above zero and at most 100%.")
    if not -1 < inputs.sip_step_up <= 1:
        raise ValueError("SIP step-up must be above -100% and at most 100%.")


def real_return(annual_return: float, inflation: float) -> float:
    return (1 + annual_return) / (1 + inflation) - 1


def fire_target_today(inputs: FireInputs) -> float:
    validate_fire(inputs)
    return inputs.monthly_expenses * 12 / inputs.withdrawal_rate


def project_fire(inputs: FireInputs, years: int | None = None) -> tuple[pd.DataFrame, float | None]:
    """Yearly trace plus first monthly FIRE crossing in years (or None).

    The crossing is evaluated monthly, not interpolated from yearly endpoints.
    """
    validate_fire(inputs)
    years = (100 - inputs.current_age) if years is None else years
    if not 1 <= years <= 100:
        raise ValueError("Projection horizon must be between 1 and 100 years.")

    balance = float(inputs.net_worth)
    invested = float(inputs.net_worth)
    annual_expenses = inputs.monthly_expenses * 12
    monthly_rate = (1 + inputs.annual_return) ** (1 / 12) - 1
    target_today = fire_target_today(inputs)
    reached = 0.0 if balance >= target_today else None

    rows = [{
        "Year": 0, "Age": inputs.current_age,
        "Net worth": balance,
        "Today's rupees": balance,
        "FIRE target": target_today,
        "Contributions": invested,
    }]
    for month in range(1, 12 * years + 1):
        year_index = (month - 1) // 12
        contribution = inputs.monthly_sip * (1 + inputs.sip_step_up) ** year_index
        balance = balance * (1 + monthly_rate) + contribution
        invested += contribution
        elapsed = month / 12
        inflation_factor = (1 + inputs.inflation) ** elapsed
        target = target_today * inflation_factor
        if reached is None and balance >= target:
            reached = elapsed
        if month % 12 == 0:
            rows.append({
                "Year": month // 12,
                "Age": inputs.current_age + month // 12,
                "Net worth": balance,
                "Today's rupees": balance / inflation_factor,
                "FIRE target": target,
                "Contributions": invested,
            })
    return pd.DataFrame(rows), reached


def retirement_snapshot(projection: pd.DataFrame, age: int) -> dict:
    match = projection.loc[projection["Age"] == age]
    if match.empty:
        raise ValueError("Target retirement age is outside the projection.")
    return match.iloc[0].to_dict()
