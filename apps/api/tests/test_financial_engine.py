from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.finance.engine import (
    calculate_holding_value,
    calculate_portfolio_value,
    calculate_total_cost,
    calculate_absolute_return,
    calculate_cagr,
    calculate_xirr,
    calculate_allocation,
    calculate_sector_exposure,
    calculate_concentration,
    calculate_drawdown,
    calculate_inflation_adjusted_value,
)
from app.finance.rounding import (
    round_currency,
    round_percent,
    round_ratio,
    round_quantity,
)


def test_holding_and_portfolio_valuation():
    holdings = [
        {"quantity": Decimal("10.5"), "current_price": Decimal("150.00"), "average_cost": Decimal("140.00")},
        {"quantity": Decimal("5"), "current_price": Decimal("300.00"), "average_cost": Decimal("280.00")},
    ]

    total_val = calculate_portfolio_value(holdings)
    total_cost = calculate_total_cost(holdings)

    # 10.5 * 150 = 1575, 5 * 300 = 1500 -> 3075
    assert total_val == Decimal("3075.00")
    # 10.5 * 140 = 1470, 5 * 280 = 1400 -> 2870
    assert total_cost == Decimal("2870.00")

    gain, pct = calculate_absolute_return(total_val, total_cost)
    assert gain == Decimal("205.00")
    assert round_percent(pct) == Decimal("0.0714")  # 205 / 2870 ≈ 0.071428


def test_cagr():
    # Doubling in 5 years: (2000 / 1000) ** (1/5) - 1 ≈ 0.148698
    start = Decimal("1000")
    end = Decimal("2000")
    years = Decimal("5")
    cagr = calculate_cagr(start, end, years)
    assert cagr is not None
    assert round_percent(cagr) == Decimal("0.1487")

    # Edge cases
    assert calculate_cagr(Decimal("0"), Decimal("1000"), Decimal("5")) is None
    assert calculate_cagr(Decimal("1000"), Decimal("1000"), Decimal("0")) is None


def test_xirr_happy_path():
    # Invest $10,000 on Jan 1, add $2,000 on July 1, worth $13,500 on Dec 31
    flows = [
        (date(2025, 1, 1), Decimal("-10000")),
        (date(2025, 7, 1), Decimal("-2000")),
        (date(2025, 12, 31), Decimal("13500")),
    ]
    rate = calculate_xirr(flows)
    assert rate is not None
    assert rate > Decimal("0.10")  # Should be around 14-16% annualized
    assert rate < Decimal("0.25")


def test_xirr_non_convergent_fallback():
    # Required by §19: unit test must include a case designed not to converge
    # Pathological sequence with extreme erratic oscillations
    flows = [
        (date(2020, 1, 1), Decimal("-1000000")),
        (date(2020, 1, 2), Decimal("100000000")),
        (date(2020, 1, 3), Decimal("-100000000")),
        (date(2020, 1, 4), Decimal("100")),
    ]
    # Either returns a valid rate or gracefully falls back to None without raising an unhandled exception
    res = calculate_xirr(flows, max_iterations=5)
    # The key requirement is that it does not crash or raise an unhandled exception
    assert res is None or isinstance(res, Decimal)

    # All negative cashflows: must return None
    all_neg = [
        (date(2025, 1, 1), Decimal("-100")),
        (date(2025, 2, 1), Decimal("-200")),
    ]
    assert calculate_xirr(all_neg) is None


def test_allocation_and_sector_exposure():
    holdings = [
        {"symbol": "AAPL", "asset_type": "stock", "sector": "Technology", "quantity": Decimal("10"), "current_price": Decimal("200")},  # 2000 (50%)
        {"symbol": "MSFT", "asset_type": "stock", "sector": "Technology", "quantity": Decimal("5"), "current_price": Decimal("300")},   # 1500 (37.5%)
        {"symbol": "JNJ", "asset_type": "stock", "sector": "Healthcare", "quantity": Decimal("5"), "current_price": Decimal("100")},    # 500 (12.5%)
    ]

    alloc = calculate_allocation(holdings)
    assert len(alloc) == 3
    assert alloc[0]["symbol"] == "AAPL"
    assert alloc[0]["weight"] == Decimal("0.5")

    sectors = calculate_sector_exposure(holdings)
    assert len(sectors) == 2
    tech = next(s for s in sectors if s["sector"] == "Technology")
    health = next(s for s in sectors if s["sector"] == "Healthcare")
    assert tech["value"] == Decimal("3500")
    assert tech["weight"] == Decimal("0.875")
    assert health["value"] == Decimal("500")
    assert health["weight"] == Decimal("0.125")


def test_concentration_and_hhi():
    # 50%, 37.5%, 12.5%
    holdings = [
        {"symbol": "AAPL", "quantity": Decimal("10"), "current_price": Decimal("200")},  # 2000
        {"symbol": "MSFT", "quantity": Decimal("5"), "current_price": Decimal("300")},   # 1500
        {"symbol": "JNJ", "quantity": Decimal("5"), "current_price": Decimal("100")},    # 500
    ]

    conc = calculate_concentration(holdings)
    assert conc["top_1_weight"] == Decimal("0.5")
    assert conc["top_3_weight"] == Decimal("1.0")
    # HHI = 50^2 + 37.5^2 + 12.5^2 = 2500 + 1406.25 + 156.25 = 4062.5
    assert conc["hhi"] == Decimal("4062.50")
    assert conc["concentration_level"] == "highly_concentrated"


def test_drawdown():
    # Peak at 100, drops to 70, recovers to 110
    prices = [Decimal("80"), Decimal("100"), Decimal("85"), Decimal("70"), Decimal("95"), Decimal("110")]
    dd = calculate_drawdown(prices)
    assert dd["peak_value"] == Decimal("100")
    assert dd["max_drawdown_amount"] == Decimal("30")
    assert dd["max_drawdown_pct"] == Decimal("0.3")


def test_inflation_adjustment():
    nominal = Decimal("10000")
    inflation_rate = Decimal("0.03")  # 3% per year
    years = Decimal("10")
    real_val = calculate_inflation_adjusted_value(nominal, inflation_rate, years)
    # 10000 / (1.03 ** 10) ≈ 7440.94
    assert Decimal("7430") < real_val < Decimal("7450")


def test_round_half_even():
    # ROUND_HALF_EVEN rounds to nearest even number for ties
    assert round_currency(Decimal("2.525")) == Decimal("2.52")
    assert round_currency(Decimal("2.535")) == Decimal("2.54")
    assert round_currency(Decimal("100.456")) == Decimal("100.46")
