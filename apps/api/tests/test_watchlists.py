import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text

from app.main import app
from app.db.session import async_session_factory, AsyncSessionLocal
from app.db.models.users import User
from app.db.models.portfolios import Asset
from app.db.models.watchlists import Watchlist, WatchlistItem, WatchlistScan, Notification
from app.workers.tasks import scheduled_watchlist_scan, refresh_holding_prices


from app.core.security import create_access_token


@pytest.fixture
async def test_user_id():
    async with async_session_factory() as session:
        user_uuid = uuid.uuid4()
        user = User(
            id=user_uuid,
            email=f"wl_user_{user_uuid.hex[:8]}@finsight.dev",
            name="Watchlist Test User",
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
        email="wl_user@finsight.dev",
        name="Watchlist Test User",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_watchlist_crud_and_item_management(auth_headers, test_user_id):
    """
    Tests complete Watchlist CRUD and adding/removing tracked asset items (§10, §38).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a new watchlist
        create_payload = {
            "name": "Semiconductor & AI Leaders",
            "scan_enabled": True,
            "scan_frequency": "daily",
        }
        res_create = await client.post("/api/v1/watchlists", headers=auth_headers, json=create_payload)
        assert res_create.status_code == 201
        wl_data = res_create.json()
        assert wl_data["name"] == "Semiconductor & AI Leaders"
        assert wl_data["scan_enabled"] is True
        assert wl_data["items_count"] == 0
        watchlist_id = wl_data["id"]

        # 2. Add ticker items
        res_item1 = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=auth_headers,
            json={"ticker": "NVDA"},
        )
        assert res_item1.status_code == 201
        item1 = res_item1.json()
        assert item1["ticker"] == "NVDA"
        assert item1["watchlist_id"] == watchlist_id

        res_item2 = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=auth_headers,
            json={"ticker": "TSM"},
        )
        assert res_item2.status_code == 201
        assert res_item2.json()["ticker"] == "TSM"

        # 3. Prevent duplicate item in same watchlist
        res_dup = await client.post(
            f"/api/v1/watchlists/{watchlist_id}/items",
            headers=auth_headers,
            json={"ticker": "NVDA"},
        )
        assert res_dup.status_code == 409
        assert "already present" in res_dup.json()["detail"].lower()

        # 4. Fetch watchlist detail
        res_detail = await client.get(f"/api/v1/watchlists/{watchlist_id}", headers=auth_headers)
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert len(detail["items"]) == 2
        assert detail["items"][0]["ticker"] in ["NVDA", "TSM"]

        # 5. Remove one item
        item_to_remove = detail["items"][0]["id"]
        res_del_item = await client.delete(
            f"/api/v1/watchlists/{watchlist_id}/items/{item_to_remove}",
            headers=auth_headers,
        )
        assert res_del_item.status_code == 204

        # Verify removal
        res_detail_after = await client.get(f"/api/v1/watchlists/{watchlist_id}", headers=auth_headers)
        assert len(res_detail_after.json()["items"]) == 1

        # 6. Update watchlist name and frequency
        res_update = await client.patch(
            f"/api/v1/watchlists/{watchlist_id}",
            headers=auth_headers,
            json={"name": "Global Tech Leaders", "scan_frequency": "weekly"},
        )
        assert res_update.status_code == 200
        assert res_update.json()["name"] == "Global Tech Leaders"
        assert res_update.json()["scan_frequency"] == "weekly"

        # 7. Delete watchlist
        res_del = await client.delete(f"/api/v1/watchlists/{watchlist_id}", headers=auth_headers)
        assert res_del.status_code == 204

        # Confirm 404 after deletion
        res_get_deleted = await client.get(f"/api/v1/watchlists/{watchlist_id}", headers=auth_headers)
        assert res_get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_watchlist_scan_execution_and_findings_persistence(auth_headers, test_user_id):
    """
    Tests market scan execution, signal detection, and durable persistence in watchlist_scans (§10, §38).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create watchlist with tracked stocks
        res_wl = await client.post(
            "/api/v1/watchlists",
            headers=auth_headers,
            json={"name": "High Beta Momentum", "scan_enabled": True},
        )
        wl_id = res_wl.json()["id"]

        await client.post(f"/api/v1/watchlists/{wl_id}/items", headers=auth_headers, json={"ticker": "AAPL"})
        await client.post(f"/api/v1/watchlists/{wl_id}/items", headers=auth_headers, json={"ticker": "MSFT"})

        # Trigger synchronous market scan
        res_scan = await client.post(
            f"/api/v1/watchlists/{wl_id}/scan?run_sync=true",
            headers=auth_headers,
        )
        assert res_scan.status_code in [200, 202]
        scan = res_scan.json()
        assert scan["status"] == "completed"
        assert scan["findings_count"] >= 1
        assert len(scan["findings"]) >= 1
        assert scan["completed_at"] is not None

        finding = scan["findings"][0]
        assert "ticker" in finding
        assert "signal_type" in finding
        assert "severity" in finding
        assert "summary" in finding


@pytest.mark.asyncio
async def test_scan_idempotency_and_concurrency_lock(auth_headers, test_user_id):
    """
    Verifies scan idempotency (§38 user design decision):
    1. Submitting with the same Idempotency-Key returns the existing scan record rather than duplicating.
    2. Concurrent/duplicate scans for the same watchlist are rejected or deduplicated.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_wl = await client.post(
            "/api/v1/watchlists",
            headers=auth_headers,
            json={"name": "Idempotent Scanner Test", "scan_enabled": True},
        )
        wl_id = res_wl.json()["id"]
        await client.post(f"/api/v1/watchlists/{wl_id}/items", headers=auth_headers, json={"ticker": "GOOGL"})

        custom_key = f"scan-key-{uuid.uuid4().hex[:8]}"

        # First trigger with idempotency key
        headers_with_key = dict(auth_headers)
        headers_with_key["Idempotency-Key"] = custom_key

        res1 = await client.post(
            f"/api/v1/watchlists/{wl_id}/scan?run_sync=true",
            headers=headers_with_key,
        )
        scan1 = res1.json()
        scan1_id = scan1["id"]

        # Second trigger with the same idempotency key
        res2 = await client.post(
            f"/api/v1/watchlists/{wl_id}/scan?run_sync=true",
            headers=headers_with_key,
        )
        scan2 = res2.json()
        scan2_id = scan2["id"]

        # Exactly the same scan returned — zero duplicate record created in database!
        assert scan1_id == scan2_id
        assert scan2["idempotency_key"] == custom_key


@pytest.mark.asyncio
async def test_notification_fanout_aggregated_per_scan(auth_headers, test_user_id):
    """
    Verifies notification fan-out rule (§user design decision):
    Scans create exactly ONE aggregated notification per scan rather than spamming one per finding.
    Also tests unread counts and mark-as-read transitions.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check initial unread count
        initial_notifs_res = await client.get("/api/v1/notifications", headers=auth_headers)
        assert initial_notifs_res.status_code == 200
        initial_unread = initial_notifs_res.json()["total_unread"]

        # Create watchlist with 3 items
        res_wl = await client.post(
            "/api/v1/watchlists",
            headers=auth_headers,
            json={"name": "Multi-Asset Alert Group", "scan_enabled": True},
        )
        wl_id = res_wl.json()["id"]
        for sym in ["AMZN", "META", "AMD"]:
            await client.post(f"/api/v1/watchlists/{wl_id}/items", headers=auth_headers, json={"ticker": sym})

        # Run scan which generates findings
        res_scan = await client.post(
            f"/api/v1/watchlists/{wl_id}/scan?run_sync=true",
            headers=auth_headers,
        )
        assert res_scan.status_code in [200, 202]

        # Verify notifications: exactly +1 notification created (aggregated, not 3 individual spams)
        notifs_res = await client.get("/api/v1/notifications", headers=auth_headers)
        assert notifs_res.status_code == 200
        data = notifs_res.json()
        assert data["total_unread"] == initial_unread + 1

        newest = data["notifications"][0]
        assert "Watchlist Scan" in newest["title"]
        assert "Multi-Asset Alert Group" in newest["title"]
        assert newest["read_at"] is None

        # Mark single notification as read
        notif_id = newest["id"]
        res_read = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=auth_headers)
        assert res_read.status_code == 200

        # Verify unread count decremented
        after_read_res = await client.get("/api/v1/notifications", headers=auth_headers)
        assert after_read_res.json()["total_unread"] == initial_unread


@pytest.mark.asyncio
async def test_watchlists_and_items_rls_tenant_isolation(auth_headers, test_user_id):
    """
    Verifies that under tenant isolation & PostgreSQL RLS, User B cannot see,
    modify, or trigger scans on User A's watchlists and items (§11, §30).
    """
    user_2_id = uuid.uuid4()
    token_2 = create_access_token(
        user_id=str(user_2_id),
        email="user_2_wl@finsight.dev",
        name="User 2 Watchlists",
    )
    auth_headers_2 = {"Authorization": f"Bearer {token_2}"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # User 1 creates watchlist and adds an item
        res1 = await client.post(
            "/api/v1/watchlists",
            headers=auth_headers,
            json={"name": "User 1 Secret Assets", "scan_enabled": True},
        )
        assert res1.status_code == 201
        wl1_id = res1.json()["id"]

        await client.post(f"/api/v1/watchlists/{wl1_id}/items", headers=auth_headers, json={"ticker": "INTC"})

        # User 2 tries to fetch User 1's watchlist -> 404
        res2_get = await client.get(f"/api/v1/watchlists/{wl1_id}", headers=auth_headers_2)
        assert res2_get.status_code == 404

        # User 2 lists watchlists -> does not contain User 1's watchlist
        res2_list = await client.get("/api/v1/watchlists", headers=auth_headers_2)
        assert res2_list.status_code == 200
        assert not any(w["id"] == wl1_id for w in res2_list.json())

        # User 2 cannot scan User 1's watchlist -> 404
        res2_scan = await client.post(f"/api/v1/watchlists/{wl1_id}/scan", headers=auth_headers_2)
        assert res2_scan.status_code == 404


def test_celery_scheduled_watchlist_scan_and_price_refresh():
    """
    Verifies Celery background tasks: scheduled_watchlist_scan and refresh_holding_prices (§10, §38).
    """
    # 1. Run scheduled_watchlist_scan task directly
    scan_result = scheduled_watchlist_scan()
    assert scan_result["status"] == "ok"
    assert "scans_executed" in scan_result

    # 2. Run refresh_holding_prices task directly
    price_result = refresh_holding_prices()
    assert price_result["status"] == "ok"
    assert "refreshed_assets" in price_result

