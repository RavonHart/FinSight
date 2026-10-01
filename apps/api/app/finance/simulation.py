from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Any
from app.finance.engine import (
    calculate_inflation_adjusted_value,
    ZERO,
    ONE,
    HUNDRED,
)
from app.finance.rounding import round_currency, round_percent

# Ensure adequate precision for financial engine calculations (§19)
getcontext().prec = 28

MONTHS_IN_YEAR = Decimal("12")


def simulate_compound_growth(
    initial_capital: Decimal,
    monthly_contribution: Decimal,
    annual_return_pct: Decimal,
    annual_inflation_pct: Decimal,
    annual_fee_pct: Decimal = ZERO,
    duration_years: int = 10,
    annual_withdrawal: Decimal = ZERO,
) -> Dict[str, Any]:
    """
    Pure-Decimal forward simulation of investment growth, recurring contributions,
    annual fee drag, inflation adjustment, and optional withdrawals (§19, §20).
    
    Closed-form monthly compounding step:
    For each month:
      1. Add monthly contribution
      2. Apply net monthly rate (annual_return - annual_fee) / 12
      3. Apply monthly withdrawal (annual_withdrawal / 12)
    """
    if duration_years < 1:
        duration_years = 1

    net_annual_return = annual_return_pct - annual_fee_pct
    monthly_rate = (net_annual_return / HUNDRED) / MONTHS_IN_YEAR
    monthly_withdrawal = annual_withdrawal / MONTHS_IN_YEAR

    current_nominal = initial_capital
    cumulative_contributions = initial_capital
    cumulative_withdrawals = ZERO
    cumulative_fees = ZERO

    yearly_snapshots: List[Dict[str, Any]] = []
    is_depleted = False
    depletion_year: Optional[int] = None

    for year in range(1, duration_years + 1):
        year_starting_nominal = current_nominal
        year_contributions = ZERO
        year_withdrawals = ZERO
        year_growth = ZERO
        year_fees = ZERO

        for _ in range(12):
            if current_nominal <= ZERO and monthly_contribution <= ZERO:
                is_depleted = True
                if depletion_year is None:
                    depletion_year = year
                current_nominal = ZERO
                break

            # 1. Contribution
            if monthly_contribution > ZERO:
                current_nominal += monthly_contribution
                year_contributions += monthly_contribution
                cumulative_contributions += monthly_contribution

            # 2. Investment growth before fee deduction
            gross_monthly_rate = (annual_return_pct / HUNDRED) / MONTHS_IN_YEAR
            growth_step = current_nominal * gross_monthly_rate
            year_growth += growth_step

            # Fee step
            fee_monthly_rate = (annual_fee_pct / HUNDRED) / MONTHS_IN_YEAR
            fee_step = current_nominal * fee_monthly_rate
            year_fees += fee_step

            # Net growth
            current_nominal += (growth_step - fee_step)
            cumulative_fees += fee_step

            # 3. Withdrawal
            if monthly_withdrawal > ZERO:
                actual_withdrawal = min(current_nominal, monthly_withdrawal)
                current_nominal -= actual_withdrawal
                year_withdrawals += actual_withdrawal
                cumulative_withdrawals += actual_withdrawal

                if current_nominal <= ZERO:
                    is_depleted = True
                    if depletion_year is None:
                        depletion_year = year
                    current_nominal = ZERO

        # Calculate purchasing power discounted by compound inflation
        real_value = calculate_inflation_adjusted_value(
            nominal_value=current_nominal,
            annual_inflation_rate=annual_inflation_pct / HUNDRED,
            years=Decimal(str(year)),
        )

        yearly_snapshots.append({
            "year": year,
            "starting_balance": round_currency(year_starting_nominal),
            "contributions": round_currency(year_contributions),
            "withdrawals": round_currency(year_withdrawals),
            "investment_growth": round_currency(year_growth),
            "fees_paid": round_currency(year_fees),
            "ending_nominal_value": round_currency(current_nominal),
            "ending_real_value": round_currency(real_value),
        })

    real_ending_value = calculate_inflation_adjusted_value(
        nominal_value=current_nominal,
        annual_inflation_rate=annual_inflation_pct / HUNDRED,
        years=Decimal(str(duration_years)),
    )

    total_gain = current_nominal + cumulative_withdrawals - cumulative_contributions

    return {
        "engine_version": "financial-engine-v1",
        "duration_years": duration_years,
        "initial_capital": round_currency(initial_capital),
        "total_contributions": round_currency(cumulative_contributions),
        "total_withdrawals": round_currency(cumulative_withdrawals),
        "total_fees_paid": round_currency(cumulative_fees),
        "nominal_ending_value": round_currency(current_nominal),
        "real_ending_value": round_currency(real_ending_value),
        "total_gain": round_currency(total_gain),
        "is_depleted": is_depleted,
        "depletion_year": depletion_year,
        "yearly_snapshots": yearly_snapshots,
    }


def run_multi_scenario_simulation(
    initial_capital: Decimal,
    monthly_contribution: Decimal,
    duration_years: int = 10,
    base_annual_return: Decimal = Decimal("7.0"),
    base_inflation: Decimal = Decimal("2.5"),
    annual_fee: Decimal = Decimal("0.25"),
    annual_withdrawal: Decimal = ZERO,
) -> Dict[str, Any]:
    """
    Executes three honest deterministic fixed-assumption scenario trajectories (§20, §32):
    - Conservative / Bear: Lower return (base - 3%), higher inflation (base + 1.5%)
    - Baseline: User-defined expected return and baseline inflation
    - Growth / Bull: Higher return (base + 3%), moderated inflation (base - 0.5%)
    """
    # Conservative / Bear
    bear_return = max(Decimal("1.0"), base_annual_return - Decimal("3.0"))
    bear_inflation = base_inflation + Decimal("1.5")
    bear_result = simulate_compound_growth(
        initial_capital=initial_capital,
        monthly_contribution=monthly_contribution,
        annual_return_pct=bear_return,
        annual_inflation_pct=bear_inflation,
        annual_fee_pct=annual_fee,
        duration_years=duration_years,
        annual_withdrawal=annual_withdrawal,
    )

    # Baseline
    base_result = simulate_compound_growth(
        initial_capital=initial_capital,
        monthly_contribution=monthly_contribution,
        annual_return_pct=base_annual_return,
        annual_inflation_pct=base_inflation,
        annual_fee_pct=annual_fee,
        duration_years=duration_years,
        annual_withdrawal=annual_withdrawal,
    )

    # Growth / Bull
    bull_return = base_annual_return + Decimal("3.0")
    bull_inflation = max(Decimal("1.0"), base_inflation - Decimal("0.5"))
    bull_result = simulate_compound_growth(
        initial_capital=initial_capital,
        monthly_contribution=monthly_contribution,
        annual_return_pct=bull_return,
        annual_inflation_pct=bull_inflation,
        annual_fee_pct=annual_fee,
        duration_years=duration_years,
        annual_withdrawal=annual_withdrawal,
    )

    return {
        "engine_version": "financial-engine-v1",
        "inputs": {
            "initial_capital": float(initial_capital),
            "monthly_contribution": float(monthly_contribution),
            "duration_years": duration_years,
            "base_annual_return": float(base_annual_return),
            "base_inflation": float(base_inflation),
            "annual_fee": float(annual_fee),
            "annual_withdrawal": float(annual_withdrawal),
        },
        "scenarios": {
            "bear": {
                "label": "Conservative / Bear Scenario",
                "assumptions": {
                    "annual_return_pct": float(bear_return),
                    "annual_inflation_pct": float(bear_inflation),
                    "annual_fee_pct": float(annual_fee),
                },
                "result": bear_result,
            },
            "base": {
                "label": "Baseline Expected Scenario",
                "assumptions": {
                    "annual_return_pct": float(base_annual_return),
                    "annual_inflation_pct": float(base_inflation),
                    "annual_fee_pct": float(annual_fee),
                },
                "result": base_result,
            },
            "bull": {
                "label": "Growth / Bull Scenario",
                "assumptions": {
                    "annual_return_pct": float(bull_return),
                    "annual_inflation_pct": float(bull_inflation),
                    "annual_fee_pct": float(annual_fee),
                },
                "result": bull_result,
            },
        },
    }
