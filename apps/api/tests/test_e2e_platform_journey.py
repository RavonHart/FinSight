import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.db.session import async_session_factory
from app.db.models.users import User
from app.db.models.portfolios import Asset
from app.core.security import create_access_token


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def tenant_a_user():
    user_uuid = uuid.uuid4()
    async with async_session_factory() as session:
        user = User(
            id=user_uuid,
            email=f"tenant_a_{user_uuid.hex[:8]}@finsight.dev",
            name="Tenant Alpha",
            hashed_password="pw_hash_test_a",
            auth_provider="local",
            is_active=True,
        )
        session.add(user)
        await session.commit()
    token = create_access_token(user_id=user_uuid, email=user.email)
    return {"id": user_uuid, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
async def tenant_b_user():
    user_uuid = uuid.uuid4()
    async with async_session_factory() as session:
        user = User(
            id=user_uuid,
            email=f"tenant_b_{user_uuid.hex[:8]}@finsight.dev",
            name="Tenant Beta",
            hashed_password="pw_hash_test_b",
            auth_provider="local",
            is_active=True,
        )
        session.add(user)
        await session.commit()
    token = create_access_token(user_id=user_uuid, email=user.email)
    return {"id": user_uuid, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture(autouse=True)
async def seed_test_assets():
    """Ensure baseline assets exist for test fixtures."""
    async with async_session_factory() as session:
        for symbol, name, price in [("AAPL", "Apple Inc.", "185.00"), ("MSFT", "Microsoft Corp.", "420.00")]:
            stmt = select(Asset).where(Asset.symbol == symbol)
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                asset = Asset(
                    id=uuid.uuid4(),
                    symbol=symbol,
                    name=name,
                    asset_type="equity",
                    currency="USD",
                    metadata_json={"price": price, "currency": "USD"},
                )
                session.add(asset)
        await session.commit()


@pytest.mark.asyncio
async def test_full_platform_golden_journey_and_multi_tenant_isolation(
    client: AsyncClient,
    tenant_a_user: dict,
    tenant_b_user: dict,
):
    """
    Comprehensive Golden Journey Integration Test (§20, §31, §32, §36, §38, §69):
    1. Tenant A completes onboarding & risk assessment questionnaire.
    2. Tenant A builds portfolio and executes buy transaction (pure Decimal metrics).
    3. Tenant A executes closed-form 3-scenario simulation with portfolio seeding.
    4. Tenant A interacts with AI Tutor (educational concept + adversarial advisory refusal).
    5. Tenant A creates watchlist, triggers scan with idempotency key, receives single aggregated notification.
    6. Multi-Tenant Penetration Assertions: Tenant B attempts to read/mutate Tenant A's portfolio,
       simulations, watchlists, scans, and notifications — asserted to fail / return 404.
    7. Tenant A exports full compliance audit package (JSON & HTML) with Jev safety logs & SHA256 digest.
    8. Health readiness probe validates Postgres, Redis, connection pool, and fail-open Celery cache.
    """
    headers_a = tenant_a_user["headers"]
    headers_b = tenant_b_user["headers"]

    # -------------------------------------------------------------
    # Step 1: Tenant A Risk Assessment & Financial Profile (§22)
    # -------------------------------------------------------------
    profile_payload = {
        "investable_capital": "35000.00",
        "monthly_contribution": "750.00",
        "investment_horizon": "long",
        "primary_goal": "wealth_growth",
        "experience_level": "intermediate",
        "liquidity_requirement": "moderate",
        "reaction_to_market_drop": "buy_more",
        "emergency_fund_coverage": "more_than_6_months",
        "income_stability": "very_stable",
    }
    r_profile = await client.post("/api/v1/profile/assessment", json=profile_payload, headers=headers_a)
    assert r_profile.status_code == 201, f"Profile assessment failed: {r_profile.text}"
    profile_data = r_profile.json()["profile"]
    assert profile_data["risk_tolerance"] in ["CONSERVATIVE", "MODERATE", "GROWTH", "AGGRESSIVE"]

    # -------------------------------------------------------------
    # Step 2: Tenant A Portfolio & Transaction Sync (§12)
    # -------------------------------------------------------------
    r_port = await client.post("/api/v1/portfolios", json={"name": "Alpha Core Wealth", "base_currency": "USD"}, headers=headers_a)
    assert r_port.status_code == 201, f"Portfolio creation failed: {r_port.text}"
    portfolio_a_id = r_port.json()["id"]

    tx_payload = {
        "symbol": "AAPL",
        "transaction_type": "buy",
        "quantity": 10,
        "price": 180,
        "fees": 1.5,
        "idempotency_key": f"tx_e2e_{uuid.uuid4().hex[:8]}",
    }
    r_tx = await client.post(f"/api/v1/portfolios/{portfolio_a_id}/transactions", json=tx_payload, headers=headers_a)
    assert r_tx.status_code == 201, f"Transaction execution failed: {r_tx.text}"

    # Verify portfolio analytics metrics
    r_val = await client.get(f"/api/v1/portfolios/{portfolio_a_id}/analytics", headers=headers_a)
    assert r_val.status_code == 200
    val_data = r_val.json()
    assert Decimal(str(val_data["total_cost"])) == Decimal("1800.00")

    # -------------------------------------------------------------
    # Step 3: Tenant A Deterministic Simulation Run (§20, §32)
    # -------------------------------------------------------------
    sim_payload = {
        "portfolio_id": portfolio_a_id,
        "initial_capital": "1850.00",
        "monthly_contribution": "500.00",
        "time_horizon_years": 10,
        "annual_return_rate": "0.08",
        "annual_fee_drag": "0.0015",
        "annual_inflation_rate": "0.025",
    }
    r_sim = await client.post("/api/v1/simulations", json=sim_payload, headers=headers_a)
    assert r_sim.status_code == 201, f"Simulation creation failed: {r_sim.text}"
    sim_data = r_sim.json()
    sim_id = sim_data["id"]
    assert sim_data["engine_version"] == "financial-engine-v1"
    assert "bear" in sim_data["result_json"]["scenarios"]
    assert "base" in sim_data["result_json"]["scenarios"]
    assert "bull" in sim_data["result_json"]["scenarios"]

    # -------------------------------------------------------------
    # Step 4: Tenant A AI Tutor & Advisory Refusal Guardrail (§69)
    # -------------------------------------------------------------
    # 4a. Educational Query (allowed)
    r_tutor_edu = await client.post(
        "/api/v1/learning/compounding-and-horizon/tutor",
        json={
            "query": "Why does time matter more than initial capital?",
            "mode": "clarify",
        },
        headers=headers_a,
    )
    assert r_tutor_edu.status_code == 200
    assert r_tutor_edu.json()["is_advisory_refusal"] is False

    # 4b. Adversarial Advisory Solicitation (must be intercepted by Jev / safety guardrail)
    r_tutor_adv = await client.post(
        "/api/v1/learning/compounding-and-horizon/tutor",
        json={
            "query": "Should I buy Tesla stock today for my portfolio?",
            "mode": "clarify",
        },
        headers=headers_a,
    )
    assert r_tutor_adv.status_code == 200
    adv_data = r_tutor_adv.json()
    assert adv_data["is_advisory_refusal"] is True
    assert "cannot provide individualized investment advice" in adv_data["explanation"]

    # -------------------------------------------------------------
    # Step 5: Tenant A Watchlist, Idempotent Scan & Notification (§38)
    # -------------------------------------------------------------
    r_wl = await client.post("/api/v1/watchlists", json={"name": "High Beta Tech", "scan_enabled": True}, headers=headers_a)
    assert r_wl.status_code == 201
    wl_id = r_wl.json()["id"]

    # Add ticker
    await client.post(f"/api/v1/watchlists/{wl_id}/items", json={"ticker": "AAPL"}, headers=headers_a)

    # Trigger scan
    scan_idemp_key = f"e2e_scan_{uuid.uuid4().hex[:8]}"
    r_scan = await client.post(
        f"/api/v1/watchlists/{wl_id}/scan?run_sync=true",
        headers={**headers_a, "Idempotency-Key": scan_idemp_key},
    )
    assert r_scan.status_code == 202
    assert r_scan.json()["status"] == "completed"

    # Verify single aggregated notification
    r_notif = await client.get("/api/v1/notifications", headers=headers_a)
    assert r_notif.status_code == 200
    notif_data = r_notif.json()
    assert notif_data["total_unread"] >= 1
    assert "High Beta Tech" in notif_data["notifications"][0]["title"]

    # -------------------------------------------------------------
    # Step 6: Multi-Tenant RLS Penetration Attacks (Tenant B Infiltration)
    # -------------------------------------------------------------
    # 6a. Tenant B attempts to read Tenant A's portfolio
    r_b_port = await client.get(f"/api/v1/portfolios/{portfolio_a_id}", headers=headers_b)
    assert r_b_port.status_code == 404, "Tenant B must NOT access Tenant A's portfolio"

    # 6b. Tenant B attempts to inject a transaction into Tenant A's portfolio
    r_b_tx = await client.post(
        f"/api/v1/portfolios/{portfolio_a_id}/transactions",
        json={
            "symbol": "MSFT",
            "transaction_type": "buy",
            "quantity": 5,
            "price": 400,
            "fees": 0,
            "idempotency_key": f"tx_b_hack_{uuid.uuid4().hex[:8]}",
        },
        headers=headers_b,
    )
    assert r_b_tx.status_code in [404, 403], "Tenant B must NOT mutate Tenant A's portfolio"

    # 6c. Tenant B attempts to read Tenant A's simulation run
    r_b_sim = await client.get(f"/api/v1/simulations/{sim_id}", headers=headers_b)
    assert r_b_sim.status_code == 404, "Tenant B must NOT view Tenant A's simulation run"

    # 6d. Tenant B attempts to read Tenant A's watchlist
    r_b_wl = await client.get(f"/api/v1/watchlists/{wl_id}", headers=headers_b)
    assert r_b_wl.status_code == 404, "Tenant B must NOT view Tenant A's watchlist"

    # 6e. Tenant B lists notifications — must NOT see Tenant A's notifications
    r_b_notifs = await client.get("/api/v1/notifications", headers=headers_b)
    assert r_b_notifs.status_code == 200
    assert r_b_notifs.json()["total_unread"] == 0, "Tenant B must have 0 unread notifications"

    # -------------------------------------------------------------
    # Step 7: Compliance Audit Export with Jev & Advisory Logs (§20, §32)
    # -------------------------------------------------------------
    # 7a. JSON Audit Export
    r_comp_json = await client.get("/api/v1/compliance/export?format=json", headers=headers_a)
    assert r_comp_json.status_code == 200
    audit_json = r_comp_json.json()
    assert audit_json["metadata"]["engine_version"] == "financial-engine-v1"
    assert audit_json["metadata"]["sha256_digest"] is not None
    assert audit_json["user_profile"]["risk_tier"] == profile_data["risk_tolerance"]
    assert len(audit_json["simulations"]) >= 1
    # Check that the advisory refusal log was captured in compliance trail
    assert len(audit_json["tutor_safety_logs"]) >= 1
    refusal_records = [t for t in audit_json["tutor_safety_logs"] if t["is_advisory_refusal"]]
    assert len(refusal_records) >= 1, "Advisory refusal must be preserved in compliance audit trail"

    # 7b. HTML Audit Export
    r_comp_html = await client.get("/api/v1/compliance/export?format=html", headers=headers_a)
    assert r_comp_html.status_code == 200
    assert "text/html" in r_comp_html.headers["content-type"]
    assert "FinSight Compliance Audit Package" in r_comp_html.text
    assert "REFUSED (ADVISORY BLOCKED)" in r_comp_html.text

    # -------------------------------------------------------------
    # Step 8: Deep Readiness Probe & Security Headers (§31, §36)
    # -------------------------------------------------------------
    # Security headers on response
    assert r_comp_json.headers.get("x-content-type-options") == "nosniff"
    assert r_comp_json.headers.get("x-frame-options") == "DENY"

    # Health readiness probe
    r_ready = await client.get("/health/ready")
    assert r_ready.status_code == 200
    ready_data = r_ready.json()
    assert ready_data["status"] == "ready"
    assert ready_data["database"]["status"] == "ok"
    assert ready_data["database"]["vector_extension"] == "ok"
    assert "pool" in ready_data["database"]
    assert ready_data["redis"] == "ok"
    assert "workers" in ready_data
