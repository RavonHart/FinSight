import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import create_access_token


@pytest.fixture
def user_1_id():
    return uuid.uuid4()


@pytest.fixture
def user_2_id():
    return uuid.uuid4()


@pytest.fixture
def auth_headers_user_1(user_1_id):
    token = create_access_token(
        user_id=str(user_1_id),
        email="portfolio_user_1@finsight.local",
        name="Portfolio User 1",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user_2(user_2_id):
    token = create_access_token(
        user_id=str(user_2_id),
        email="portfolio_user_2@finsight.local",
        name="Portfolio User 2",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_portfolio_crud_and_isolation(auth_headers_user_1, auth_headers_user_2):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create a virtual portfolio for user 1
        create_payload = {
            "name": "Retirement Growth Virtual",
            "base_currency": "USD",
            "portfolio_type": "virtual",
            "is_virtual": True,
        }
        res = await client.post("/api/v1/portfolios", json=create_payload, headers=auth_headers_user_1)
        assert res.status_code == 201
        p_data = res.json()
        portfolio_id = p_data["id"]
        assert p_data["name"] == "Retirement Growth Virtual"
        assert p_data["is_virtual"] is True

        # 2. Verify user 1 can list their portfolio
        list_res = await client.get("/api/v1/portfolios", headers=auth_headers_user_1)
        assert list_res.status_code == 200
        assert any(p["id"] == portfolio_id for p in list_res.json())

        # 3. Verify user 2 CANNOT access or list user 1's portfolio
        u2_list = await client.get("/api/v1/portfolios", headers=auth_headers_user_2)
        assert u2_list.status_code == 200
        assert not any(p["id"] == portfolio_id for p in u2_list.json())

        u2_direct = await client.get(f"/api/v1/portfolios/{portfolio_id}", headers=auth_headers_user_2)
        assert u2_direct.status_code == 404

        # 4. Update portfolio
        update_res = await client.put(
            f"/api/v1/portfolios/{portfolio_id}",
            json={"name": "All-Weather Virtual Strategy"},
            headers=auth_headers_user_1,
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "All-Weather Virtual Strategy"


@pytest.mark.asyncio
async def test_holdings_crud_and_valuation(auth_headers_user_1):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create portfolio
        p_res = await client.post(
            "/api/v1/portfolios",
            json={"name": "Tech Allocation", "base_currency": "USD"},
            headers=auth_headers_user_1,
        )
        portfolio_id = p_res.json()["id"]

        # Add AAPL holding
        h_res = await client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "average_cost": 200,
                "current_price": 225,
            },
            headers=auth_headers_user_1,
        )
        assert h_res.status_code == 201
        h_data = h_res.json()
        holding_id = h_data["id"]
        assert h_data["symbol"] == "AAPL"
        assert Decimal(str(h_data["quantity"])) == Decimal("10")
        assert Decimal(str(h_data["current_value"])) == Decimal("2250")
        assert Decimal(str(h_data["unrealized_gain_loss"])) == Decimal("250")

        # Update holding quantity
        up_res = await client.put(
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
            json={"quantity": 15},
            headers=auth_headers_user_1,
        )
        assert up_res.status_code == 200
        assert Decimal(str(up_res.json()["quantity"])) == Decimal("15")
        assert Decimal(str(up_res.json()["current_value"])) == Decimal("3375")

        # Delete holding
        del_res = await client.delete(
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}",
            headers=auth_headers_user_1,
        )
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_transaction_idempotency_and_holding_sync(auth_headers_user_1):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        p_res = await client.post(
            "/api/v1/portfolios",
            json={"name": "Transaction Sync Portfolio", "base_currency": "USD"},
            headers=auth_headers_user_1,
        )
        portfolio_id = p_res.json()["id"]

        idempotency_key = f"tx-test-{uuid.uuid4()}"

        tx_payload = {
            "symbol": "MSFT",
            "transaction_type": "buy",
            "quantity": 5,
            "price": 400,
            "fees": 5,
            "idempotency_key": idempotency_key,
        }

        # 1. Record buy transaction
        tx1 = await client.post(
            f"/api/v1/portfolios/{portfolio_id}/transactions",
            json=tx_payload,
            headers=auth_headers_user_1,
        )
        assert tx1.status_code == 201
        tx1_id = tx1.json()["id"]

        # 2. Retrying identical request with same idempotency key returns the existing transaction (§45)
        tx2 = await client.post(
            f"/api/v1/portfolios/{portfolio_id}/transactions",
            json=tx_payload,
            headers=auth_headers_user_1,
        )
        assert tx2.status_code == 201
        assert tx2.json()["id"] == tx1_id

        # 3. Verify holding was created and synced
        holdings_res = await client.get(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            headers=auth_headers_user_1,
        )
        assert holdings_res.status_code == 200
        holdings = holdings_res.json()
        assert len(holdings) == 1
        assert holdings[0]["symbol"] == "MSFT"
        assert Decimal(str(holdings[0]["quantity"])) == Decimal("5")


@pytest.mark.asyncio
async def test_deterministic_portfolio_analytics(auth_headers_user_1):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create virtual portfolio
        p_res = await client.post(
            "/api/v1/portfolios",
            json={"name": "Core Balanced Fund", "base_currency": "USD", "is_virtual": True},
            headers=auth_headers_user_1,
        )
        portfolio_id = p_res.json()["id"]

        # Add 3 holdings across different sectors
        # 1. AAPL: 10 shares @ 200 cost, 225 price -> Val: 2250, Cost: 2000 (Tech)
        await client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "AAPL", "quantity": 10, "average_cost": 200, "current_price": 225},
            headers=auth_headers_user_1,
        )
        # 2. JNJ: 10 shares @ 150 cost, 160 price -> Val: 1600, Cost: 1500 (Healthcare)
        await client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "JNJ", "quantity": 10, "average_cost": 150, "current_price": 160},
            headers=auth_headers_user_1,
        )
        # 3. BND: 20 shares @ 75 cost, 70 price -> Val: 1400, Cost: 1500 (Fixed Income)
        await client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings",
            json={"symbol": "BND", "quantity": 20, "average_cost": 75, "current_price": 70},
            headers=auth_headers_user_1,
        )

        # Total Val: 2250 + 1600 + 1400 = 5250
        # Total Cost: 2000 + 1500 + 1500 = 5000
        # Gain: +250 (+5.0%)

        # Query analytics endpoint
        analytics_res = await client.get(
            f"/api/v1/portfolios/{portfolio_id}/analytics",
            headers=auth_headers_user_1,
        )
        assert analytics_res.status_code == 200
        data = analytics_res.json()

        assert Decimal(str(data["total_value"])) == Decimal("5250")
        assert Decimal(str(data["total_cost"])) == Decimal("5000")
        assert Decimal(str(data["unrealized_gain_loss"])) == Decimal("250")
        assert Decimal(str(data["unrealized_gain_loss_pct"])) == Decimal("0.05")

        # Verify allocations sum to 100%
        allocs = data["allocations"]
        assert len(allocs) == 3
        weights_sum = sum(Decimal(str(a["weight"])) for a in allocs)
        assert round(weights_sum, 4) == Decimal("1.0000")

        # Verify sector exposures
        sectors = data["sector_exposures"]
        assert len(sectors) >= 2
        sector_weights_sum = sum(Decimal(str(s["weight"])) for s in sectors)
        assert round(sector_weights_sum, 4) == Decimal("1.0000")

        # Verify concentration metrics
        conc = data["concentration"]
        assert Decimal(str(conc["top_1_weight"])) > 0
        assert Decimal(str(conc["hhi"])) > 0
        assert conc["concentration_level"] in ["diversified", "moderately_concentrated", "highly_concentrated"]
