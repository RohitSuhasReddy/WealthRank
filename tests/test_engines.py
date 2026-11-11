from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from wealthrank.analytics import PERIODS, allocation, period_returns, risk_metrics
from wealthrank.evaluation import ndcg_at_k, precision_at_k, run_synthetic_lab
from wealthrank.fire import FireInputs, fire_target_today, project_fire, real_return, retirement_expenses, first_year_withdrawal


BASE = FireInputs(current_age=25, monthly_expenses=50_000, net_worth=1_000_000,
                  annual_return=.10, inflation=.06, monthly_sip=20_000)


def test_fire_target_and_inflation():
    assert fire_target_today(BASE) == pytest.approx(15_000_000)
    assert real_return(.10, .06) == pytest.approx(1.10 / 1.06 - 1)
    p, _ = project_fire(BASE, years=10)
    row = p.iloc[-1]
    assert row["FIRE target"] == pytest.approx(15_000_000 * 1.06 ** 10)
    assert row["Today's rupees"] == pytest.approx(row["Net worth"] / 1.06 ** 10)


def test_fire_sip_and_initial_crossing():
    a, _ = project_fire(replace(BASE, monthly_sip=0), years=20)
    b, _ = project_fire(BASE, years=20)
    assert b.iloc[-1]["Net worth"] > a.iloc[-1]["Net worth"]
    already = replace(BASE, net_worth=20_000_000)
    _, time = project_fire(already, years=10)
    assert time == 0


def test_negative_return_and_bad_inputs():
    p, _ = project_fire(replace(BASE, annual_return=-.2, inflation=0, monthly_sip=0), years=1)
    assert p.iloc[-1]["Net worth"] == pytest.approx(800_000, abs=.01)
    with pytest.raises(ValueError):
        project_fire(replace(BASE, withdrawal_rate=0))


def test_risk_uses_actual_observations():
    dates = pd.bdate_range("2024-01-01", periods=130)
    asset = pd.Series(100 * (1.001 ** np.arange(130)), index=dates)
    positions = [{"name":"A","asset_class":"Stock","sector":"Technology",
                  "value_inr":1000,"history_inr":asset}]
    result = risk_metrics(positions)
    assert result["total"] == 1000
    assert result["concentration"] == 1
    assert result["volatility"] is not None
    assert result["observations"] >= 60
    assert allocation(positions).iloc[0]["Weight"] == 1


def test_period_returns_require_history():
    dates = pd.bdate_range("2026-01-01", periods=20)
    returns = period_returns(pd.Series(np.arange(20) + 100, index=dates))
    assert returns["1W"] is not None
    assert returns["5Y"] is None
    assert set(returns) == set(PERIODS)


def test_ranking_and_repeatability():
    relevance = np.array([2, 1, 0, 2, 0])
    ranks = np.array([0, 3, 1, 2, 4])
    assert ndcg_at_k(relevance, ranks, 2) == pytest.approx(1)
    assert precision_at_k(relevance, ranks, 2) == 1
    assert run_synthetic_lab() == run_synthetic_lab()


def test_retirement_expenses_preserve_real_lifestyle():
    future = retirement_expenses(BASE, retirement_age=55)
    expected_monthly = BASE.monthly_expenses * (1 + BASE.inflation) ** 30
    assert future["monthly"] == pytest.approx(expected_monthly)
    assert future["annual"] == pytest.approx(expected_monthly * 12)
    assert future["corpus"] == pytest.approx(future["annual"] / BASE.withdrawal_rate)
    assert future["corpus"] == pytest.approx(fire_target_today(BASE) * (1 + BASE.inflation) ** 30)


def test_expenses_stay_unchanged_without_inflation():
    flat = replace(BASE, inflation=0)
    result = retirement_expenses(flat, retirement_age=60)
    assert result["monthly"] == flat.monthly_expenses
    assert result["annual"] == flat.monthly_expenses * 12


def test_withdrawal_rate_is_budget_not_inflation():
    corpus = 25_000_000
    assert first_year_withdrawal(corpus, .04) == 1_000_000
    assert first_year_withdrawal(corpus, .03) == 750_000
    with pytest.raises(ValueError):
        first_year_withdrawal(corpus, 0)
    with pytest.raises(ValueError):
        retirement_expenses(BASE, retirement_age=BASE.current_age)
