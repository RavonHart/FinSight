import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import create_access_token
from app.db.session import async_session_factory
from app.db.models.users import User
from app.db.models.portfolios import Portfolio, Holding, Asset
from app.finance.simulation import simulate_compound_growth, run_multi_scenario_simulation
from app.domains.simulations.schemas import SimulationRequest


@pytest.fixture
async def test_user_id():
    async with async_session_factory() as session:
        user_uuid = uuid.uuid4()
        user = User(
            id=user_uuid,
            email=f"sim_user_{user_uuid.hex[:8]}@finsight.dev",
            name="Simulation Test User",
            hashed_password="hashed_pw_test",
            auth_provider="local",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        return user.id


@pytest.fixture
def auth_headers(test_user_id):
    token = create_access_token(
        user_id=str(test_user_id),
        email="sim_user@finsight.dev",
        name="Simulation Test User",
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Financial Engine Simulation Math Tests (§19, §20)
# ---------------------------------------------------------------------------

def test_simulation_engine_compound_growth():
    """
    Tests forward compounding of $10,000 initial capital, $500 monthly contribution,
    7% annual return, 2.5% inflation, 0.25% fee over 5 years.
    """
    result = simulate_compound_growth(
        initial_capital=Decimal("10000.00"),
        monthly_contribution=Decimal("500.00"),
        annual_return_pct=Decimal("7.0"),
        annual_inflation_pct=Decimal("2.5"),
        annual_fee_pct=Decimal("0.25"),
        duration_years=5,
    )

    assert result["engine_version"] == "financial-engine-v1"
    assert result["duration_years"] == 5
    assert result["initial_capital"] == Decimal("10000.00")
    # Total contributions = 10000 + (500 * 60) = 40000
    assert result["total_contributions"] == Decimal("40000.00")
    assert result["nominal_ending_value"] > Decimal("40000.00")
    # Real value is discounted for inflation
    assert result["real_ending_value"] < result["nominal_ending_value"]
    assert result["total_fees_paid"] > Decimal("0.00")
    assert result["is_depleted"] is False
    assert len(result["yearly_snapshots"]) == 5

    # Check snapshot structure
    snap_1 = result["yearly_snapshots"][0]
    assert snap_1["year"] == 1
    assert snap_1["starting_balance"] == Decimal("10000.00")
    assert snap_1["contributions"] == Decimal("6000.00")
    assert snap_1["ending_nominal_value"] > Decimal("16000.00")


def test_simulation_engine_withdrawal_depletion():
    """
    Tests portfolio depletion when annual withdrawals exceed return and capital (§20).
    """
    result = simulate_compound_growth(
        initial_capital=Decimal("10000.00"),
        monthly_contribution=Decimal("0.00"),
        annual_return_pct=Decimal("3.0"),
        annual_inflation_pct=Decimal("2.0"),
        duration_years=10,
        annual_withdrawal=Decimal("4000.00"),
    )

    assert result["is_depleted"] is True
    assert result["depletion_year"] is not None
    assert 2 <= result["depletion_year"] <= 4
    assert result["nominal_ending_value"] == Decimal("0.00")


def test_simulation_multi_scenario_deterministic_honesty():
    """
    Verifies that multi-scenario analysis returns 3 distinct deterministic trajectories
    (Bear, Base, Bull) without misleading distribution or Monte Carlo fan (§20, §32).
    """
    multi = run_multi_scenario_simulation(
        initial_capital=Decimal("20000.00"),
        monthly_contribution=Decimal("1000.00"),
        duration_years=10,
        base_annual_return=Decimal("8.0"),
        base_inflation=Decimal("3.0"),
        annual_fee=Decimal("0.5"),
    )

    scenarios = multi["scenarios"]
    assert "bear" in scenarios
    assert "base" in scenarios
    assert "bull" in scenarios

    bear_val = scenarios["bear"]["result"]["nominal_ending_value"]
    base_val = scenarios["base"]["result"]["nominal_ending_value"]
    bull_val = scenarios["bull"]["result"]["nominal_ending_value"]

    # Trajectories are strictly ordered
    assert bear_val < base_val < bull_val


# ---------------------------------------------------------------------------
# API Endpoint Integration Tests (§10, §28, §58)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_simulation_api_create_and_fetch(auth_headers, test_user_id):
    """Tests POST /api/v1/simulations and GET /api/v1/simulations/{id}."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create simulation
        create_res = await client.post(
            "/api/v1/simulations",
            json={
                "initial_capital": 15000.0,
                "monthly_contribution": 750.0,
                "duration_years": 15,
                "annual_return_pct": 7.5,
                "annual_inflation_pct": 2.5,
                "annual_fee_pct": 0.3,
                "annual_withdrawal": 0.0,
            },
            headers=auth_headers,
        )
        assert create_res.status_code == 201
        data = create_res.json()
        assert "id" in data
        assert data["engine_version"] == "financial-engine-v1"
        assert "scenarios" in data["result_json"]
        sim_id = data["id"]

        # Fetch simulation
        get_res = await client.get(f"/api/v1/simulations/{sim_id}", headers=auth_headers)
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["id"] == sim_id
        assert get_data["result_json"]["scenarios"]["base"]["result"]["nominal_ending_value"] > 0

        # List simulations
        list_res = await client.get("/api/v1/simulations", headers=auth_headers)
        assert list_res.status_code == 200
        runs_list = list_res.json()
        assert len(runs_list) >= 1
        assert any(r["id"] == sim_id for r in runs_list)


@pytest.mark.asyncio
async def test_simulation_portfolio_seeding(auth_headers, test_user_id):
    """Tests seeding initial capital dynamically from an existing portfolio."""
    async with async_session_factory() as session:
        port = Portfolio(
            id=uuid.uuid4(),
            user_id=test_user_id,
            name="Seed Tech Portfolio",
            base_currency="USD",
        )
        session.add(port)
        await session.flush()

        sym1 = f"TEST_A_{uuid.uuid4().hex[:6]}"
        sym2 = f"TEST_B_{uuid.uuid4().hex[:6]}"
        a1 = Asset(
            id=uuid.uuid4(),
            symbol=sym1,
            name="Test Asset 1",
            asset_type="stock",
            currency="USD",
        )
        a2 = Asset(
            id=uuid.uuid4(),
            symbol=sym2,
            name="Test Asset 2",
            asset_type="stock",
            currency="USD",
        )
        session.add_all([a1, a2])
        await session.flush()

        # Add 2 holdings: 10 * 100 = 1000, 5 * 200 = 1000 -> Total = 2000
        h1 = Holding(
            id=uuid.uuid4(),
            portfolio_id=port.id,
            asset_id=a1.id,
            quantity=Decimal("10.0"),
            average_cost=Decimal("90.0"),
            current_price=Decimal("100.0"),
        )
        h2 = Holding(
            id=uuid.uuid4(),
            portfolio_id=port.id,
            asset_id=a2.id,
            quantity=Decimal("5.0"),
            average_cost=Decimal("180.0"),
            current_price=Decimal("200.0"),
        )
        session.add_all([h1, h2])
        await session.commit()
        port_id_str = str(port.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Submit simulation with initial_capital=0 and portfolio_id
        res = await client.post(
            "/api/v1/simulations",
            json={
                "portfolio_id": port_id_str,
                "initial_capital": 0.0,
                "monthly_contribution": 100.0,
                "duration_years": 5,
                "annual_return_pct": 6.0,
                "annual_inflation_pct": 2.0,
            },
            headers=auth_headers,
        )
        assert res.status_code == 201
        data = res.json()
        # Seeded capital should be 2000.0
        assert data["input_json"]["initial_capital"] == 2000.0


@pytest.mark.asyncio
async def test_simulation_tenant_isolation(auth_headers):
    """Ensures a user cannot view or access another user's simulation run (§11, §30)."""
    # Create another user and simulation
    async with async_session_factory() as session:
        other_user = User(
            id=uuid.uuid4(),
            email=f"other_{uuid.uuid4().hex[:6]}@finsight.dev",
            name="Other User",
            hashed_password="pw",
            auth_provider="local",
            is_active=True,
        )
        session.add(other_user)
        await session.commit()
        other_token = create_access_token(
            user_id=str(other_user.id),
            email=other_user.email,
            name=other_user.name,
        )
        other_headers = {"Authorization": f"Bearer {other_token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User A creates a run
        a_res = await client.post(
            "/api/v1/simulations",
            json={"initial_capital": 5000.0, "monthly_contribution": 200.0, "duration_years": 5},
            headers=auth_headers,
        )
        run_id = a_res.json()["id"]

        # Other user attempts to fetch User A's run -> 404
        unauth_res = await client.get(f"/api/v1/simulations/{run_id}", headers=other_headers)
        assert unauth_res.status_code == 404
