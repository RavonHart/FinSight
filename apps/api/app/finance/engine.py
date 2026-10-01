import math
from datetime import datetime, date
from decimal import Decimal, getcontext
from typing import Dict, List, Optional, Tuple, Any

from app.finance.rounding import (
    round_currency,
    round_percent,
    round_ratio,
    round_quantity,
)

# Ensure adequate precision for intermediate Financial Engine steps (§19)
getcontext().prec = 28

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def calculate_holding_value(quantity: Decimal, price: Optional[Decimal]) -> Decimal:
    """Calculates holding value from quantity and current price."""
    if price is None or price <= ZERO or quantity <= ZERO:
        return ZERO
    return quantity * price


def calculate_portfolio_value(holdings: List[Dict[str, Any]]) -> Decimal:
    """Calculates total portfolio value across all holdings (§19)."""
    total = ZERO
    for h in holdings:
        qty = Decimal(str(h.get("quantity", 0)))
        price = Decimal(str(h.get("current_price", 0))) if h.get("current_price") is not None else ZERO
        total += calculate_holding_value(qty, price)
    return total


def calculate_total_cost(holdings: List[Dict[str, Any]]) -> Decimal:
    """Calculates total cost basis across all holdings."""
    total = ZERO
    for h in holdings:
        qty = Decimal(str(h.get("quantity", 0)))
        cost = Decimal(str(h.get("average_cost", 0))) if h.get("average_cost") is not None else ZERO
        if qty > ZERO and cost > ZERO:
            total += qty * cost
    return total


def calculate_absolute_return(
    total_value: Decimal, total_cost: Decimal
) -> Tuple[Decimal, Optional[Decimal]]:
    """
    Calculates absolute dollar gain/loss and percentage return (§19).
    Returns (dollar_gain_loss, percent_gain_loss).
    """
    gain_loss = total_value - total_cost
    if total_cost > ZERO:
        pct_return = gain_loss / total_cost
        return gain_loss, pct_return
    return gain_loss, None


def calculate_cagr(
    start_value: Decimal, end_value: Decimal, years: Decimal
) -> Optional[Decimal]:
    """
    Calculates Compound Annual Growth Rate (CAGR) (§19).
    Formula: (end_value / start_value) ** (1 / years) - 1
    """
    if start_value <= ZERO or end_value <= ZERO or years <= ZERO:
        return None
    try:
        ratio = float(end_value / start_value)
        power = float(ONE / years)
        cagr_float = (ratio ** power) - 1.0
        return Decimal(str(round(cagr_float, 8)))
    except (ValueError, OverflowError, ZeroDivisionError):
        return None


def calculate_xirr(
    cash_flows: List[Tuple[Any, Decimal]],
    max_iterations: int = 100,
    tolerance: Decimal = Decimal("1e-6"),
) -> Optional[Decimal]:
    """
    Calculates Extended Internal Rate of Return (XIRR) using bounded Newton-Raphson (§19).
    cash_flows: list of (date, amount) tuples.
    Negative amounts indicate outflows/investments; positive amounts indicate inflows/current value.
    Returns None if cash flows lack sign changes, or if numerical method fails to converge.
    """
    if len(cash_flows) < 2:
        return None

    # Verify both positive and negative cash flows exist
    has_positive = any(cf[1] > ZERO for cf in cash_flows)
    has_negative = any(cf[1] < ZERO for cf in cash_flows)
    if not (has_positive and has_negative):
        return None

    # Parse and sort cash flows by date
    parsed_flows: List[Tuple[date, Decimal]] = []
    for d, amt in cash_flows:
        flow_date: date
        if isinstance(d, datetime):
            flow_date = d.date()
        elif isinstance(d, date):
            flow_date = d
        elif isinstance(d, str):
            flow_date = datetime.fromisoformat(d.replace("Z", "+00:00")).date()
        else:
            return None
        parsed_flows.append((flow_date, Decimal(str(amt))))

    parsed_flows.sort(key=lambda x: x[0])
    start_date = parsed_flows[0][0]

    # Precalculate time intervals in years
    intervals: List[Tuple[float, float]] = []
    for dt, amt in parsed_flows:
        day_diff = (dt - start_date).days
        years_diff = day_diff / 365.0
        intervals.append((years_diff, float(amt)))

    # Initial guess
    rate = 0.10

    for _ in range(max_iterations):
        if rate <= -0.9999:
            rate = -0.9990

        # Calculate NPV and derivative
        npv = 0.0
        d_npv = 0.0
        one_plus_r = 1.0 + rate

        for t, c in intervals:
            if t == 0.0:
                npv += c
            else:
                discount = one_plus_r ** t
                if discount == 0.0:
                    return None
                npv += c / discount
                d_npv -= (t * c) / (discount * one_plus_r)

        if abs(npv) < float(tolerance):
            return Decimal(str(round(rate, 8)))

        if abs(d_npv) < 1e-12:
            # Derivative too close to zero; numerical instability
            return None

        new_rate = rate - (npv / d_npv)

        # Enforce rate boundary step limit
        if new_rate < -0.99:
            new_rate = -0.99 + abs(rate) * 0.1

        if abs(new_rate - rate) < float(tolerance):
            return Decimal(str(round(new_rate, 8)))

        rate = new_rate

    # Failed to converge within max_iterations (§19 fallback)
    return None


def calculate_allocation(
    holdings: List[Dict[str, Any]], total_value: Optional[Decimal] = None
) -> List[Dict[str, Any]]:
    """
    Computes percentage portfolio allocation per holding (§19).
    Sum of weights will equal 1.0 (or 0 if empty).
    """
    if total_value is None:
        total_value = calculate_portfolio_value(holdings)

    if total_value <= ZERO:
        return [
            {
                "asset_id": h.get("asset_id"),
                "symbol": h.get("symbol", "N/A"),
                "name": h.get("name", ""),
                "asset_type": h.get("asset_type", "stock"),
                "value": ZERO,
                "weight": ZERO,
                "weight_pct": ZERO,
            }
            for h in holdings
        ]

    allocations = []
    for h in holdings:
        qty = Decimal(str(h.get("quantity", 0)))
        price = Decimal(str(h.get("current_price", 0))) if h.get("current_price") is not None else ZERO
        val = calculate_holding_value(qty, price)
        weight = val / total_value
        allocations.append({
            "asset_id": h.get("asset_id"),
            "symbol": h.get("symbol", "N/A"),
            "name": h.get("name", ""),
            "asset_type": h.get("asset_type", "stock"),
            "value": val,
            "weight": weight,
            "weight_pct": weight * HUNDRED,
        })

    # Sort descending by value
    allocations.sort(key=lambda x: x["value"], reverse=True)
    return allocations


def calculate_sector_exposure(
    holdings: List[Dict[str, Any]], total_value: Optional[Decimal] = None
) -> List[Dict[str, Any]]:
    """
    Computes sector exposure distribution across holdings (§19).
    """
    if total_value is None:
        total_value = calculate_portfolio_value(holdings)

    sector_totals: Dict[str, Decimal] = {}

    for h in holdings:
        qty = Decimal(str(h.get("quantity", 0)))
        price = Decimal(str(h.get("current_price", 0))) if h.get("current_price") is not None else ZERO
        val = calculate_holding_value(qty, price)
        sector = h.get("sector") or "Unassigned"
        sector_totals[sector] = sector_totals.get(sector, ZERO) + val

    exposures = []
    for sector, val in sector_totals.items():
        weight = (val / total_value) if total_value > ZERO else ZERO
        exposures.append({
            "sector": sector,
            "value": val,
            "weight": weight,
            "weight_pct": weight * HUNDRED,
        })

    exposures.sort(key=lambda x: x["value"], reverse=True)
    return exposures


def calculate_concentration(
    holdings: List[Dict[str, Any]], total_value: Optional[Decimal] = None
) -> Dict[str, Any]:
    """
    Calculates portfolio concentration metrics: Top 1, Top 3, Top 5 weights, and HHI (§19).
    HHI (Herfindahl-Hirschman Index) on scale 0 - 10,000.
    """
    allocations = calculate_allocation(holdings, total_value)
    if not allocations:
        return {
            "top_1_weight": ZERO,
            "top_3_weight": ZERO,
            "top_5_weight": ZERO,
            "hhi": ZERO,
            "concentration_level": "diversified",
        }

    weights = [a["weight"] for a in allocations]

    top_1 = weights[0] if len(weights) > 0 else ZERO
    top_3 = sum(weights[:3]) if len(weights) >= 3 else sum(weights)
    top_5 = sum(weights[:5]) if len(weights) >= 5 else sum(weights)

    # HHI = sum of (weight in percent)^2
    hhi = sum((w * HUNDRED) ** 2 for w in weights)

    # Concentration rating
    if hhi > Decimal("2500"):
        level = "highly_concentrated"
    elif hhi > Decimal("1500"):
        level = "moderately_concentrated"
    else:
        level = "diversified"

    return {
        "top_1_weight": top_1,
        "top_3_weight": top_3,
        "top_5_weight": top_5,
        "hhi": hhi,
        "concentration_level": level,
    }


def calculate_drawdown(values: List[Decimal]) -> Dict[str, Any]:
    """
    Calculates maximum drawdown from a sequence of portfolio values (§19).
    Returns max drawdown amount, max drawdown percentage, and the peak/trough corresponding to that drawdown.
    """
    if not values:
        return {
            "max_drawdown_amount": ZERO,
            "max_drawdown_pct": ZERO,
            "peak_value": ZERO,
            "trough_value": ZERO,
        }

    running_peak = values[0]
    max_dd_amount = ZERO
    max_dd_pct = ZERO
    peak_at_max_dd = values[0]
    trough_at_max_dd = values[0]

    for v in values:
        if v > running_peak:
            running_peak = v
        dd_amount = running_peak - v
        if running_peak > ZERO:
            dd_pct = dd_amount / running_peak
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                max_dd_amount = dd_amount
                peak_at_max_dd = running_peak
                trough_at_max_dd = v

    return {
        "max_drawdown_amount": max_dd_amount,
        "max_drawdown_pct": max_dd_pct,
        "peak_value": peak_at_max_dd,
        "trough_value": trough_at_max_dd,
    }


def calculate_inflation_adjusted_value(
    nominal_value: Decimal, annual_inflation_rate: Decimal, years: Decimal
) -> Decimal:
    """
    Computes purchasing power discounted by compound inflation (§19).
    Formula: nominal_value / ((1 + annual_inflation_rate) ** years)
    """
    if nominal_value <= ZERO or years <= ZERO:
        return nominal_value
    try:
        rate_float = float(annual_inflation_rate)
        years_float = float(years)
        discount = (1.0 + rate_float) ** years_float
        if discount == 0.0:
            return nominal_value
        result = float(nominal_value) / discount
        return Decimal(str(round(result, 4)))
    except (ValueError, OverflowError):
        return nominal_value
