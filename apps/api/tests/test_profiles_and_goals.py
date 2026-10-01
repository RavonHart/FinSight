import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_questionnaire_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/profile/questionnaire")
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) >= 9
    assert questions[0]["id"] == "investable_capital"
    assert "why_it_matters" in questions[0]


@pytest.mark.asyncio
async def test_unauthenticated_profile_endpoints_rejected(client: AsyncClient):
    res_get = await client.get("/api/v1/profile")
    assert res_get.status_code == 401

    res_post = await client.post("/api/v1/profile/assessment", json={})
    assert res_post.status_code == 401

    res_goals = await client.get("/api/v1/goals")
    assert res_goals.status_code == 401


@pytest.mark.asyncio
async def test_profile_assessment_and_versioning_flow(client: AsyncClient):
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id=user_id, email=f"investor_{uuid.uuid4().hex[:8]}@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initially profile is 404
    res_init = await client.get("/api/v1/profile", headers=headers)
    assert res_init.status_code == 404

    # 2. Submit valid assessment
    submission = {
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
    submit_res = await client.post("/api/v1/profile/assessment", headers=headers, json=submission)
    assert submit_res.status_code == 201
    data = submit_res.json()

    assert data["profile"]["profile_version"] == 1
    assert data["profile"]["investable_capital"] == "35000.00"
    assert data["profile"]["risk_tolerance"] == "AGGRESSIVE"
    assert data["profile"]["risk_capacity"] == "HIGH"

    assert data["assessment"]["assessment_version"] == 1
    assert data["assessment"]["confidence"] >= 0.80
    assert data["assessment"]["routing_action"] == "continue"
    assert len(data["assessment"]["jev_dimensions"]) == 5

    # 3. Retrieve active profile
    profile_res = await client.get("/api/v1/profile", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["profile_version"] == 1

    # 4. Retrieve latest assessment
    assess_res = await client.get("/api/v1/profile/assessment", headers=headers)
    assert assess_res.status_code == 200
    assert assess_res.json()["assessment_version"] == 1

    # 5. Submit revised assessment -> increments profile_version to 2
    revised_submission = dict(submission)
    revised_submission["reaction_to_market_drop"] = "panic_sell"
    revised_submission["emergency_fund_coverage"] = "less_than_3_months"
    revised_res = await client.post("/api/v1/profile/assessment", headers=headers, json=revised_submission)
    assert revised_res.status_code == 201
    revised_data = revised_res.json()
    assert revised_data["profile"]["profile_version"] == 2
    assert revised_data["profile"]["risk_tolerance"] == "CONSERVATIVE"
    assert revised_data["profile"]["risk_capacity"] == "LOW"

    # 6. Update profile attributes directly
    update_res = await client.put(
        "/api/v1/profile",
        headers=headers,
        json={"monthly_contribution": "1200.00"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["monthly_contribution"] == "1200.00"
    assert update_res.json()["profile_version"] == 3


@pytest.mark.asyncio
async def test_profile_conflicting_clarification_routing(client: AsyncClient):
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id=user_id, email=f"conflicted_{uuid.uuid4().hex[:8]}@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    submission = {
        "investable_capital": "10000.00",
        "monthly_contribution": "200.00",
        "investment_horizon": "medium",
        "primary_goal": "wealth_growth",
        "experience_level": "beginner",
        "liquidity_requirement": "immediate",
        "reaction_to_market_drop": "panic_sell",
        "emergency_fund_coverage": "less_than_3_months",
        "income_stability": "unstable",
        "is_conflicting_test": True,  # Triggers low confidence routing
    }
    res = await client.post("/api/v1/profile/assessment", headers=headers, json=submission)
    assert res.status_code == 201
    data = res.json()
    assert data["assessment"]["routing_action"] == "request_clarification"
    assert data["assessment"]["follow_up_prompt"] is not None


@pytest.mark.asyncio
async def test_user_profile_ownership_isolation(client: AsyncClient):
    # User A creates profile
    user_a_id = str(uuid.uuid4())
    token_a = create_access_token(user_id=user_a_id, email=f"usera_{uuid.uuid4().hex[:8]}@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    submission = {
        "investable_capital": "50000.00",
        "monthly_contribution": "1000.00",
        "investment_horizon": "long",
        "primary_goal": "retirement",
        "experience_level": "advanced",
        "liquidity_requirement": "low",
        "reaction_to_market_drop": "buy_more",
        "emergency_fund_coverage": "more_than_6_months",
        "income_stability": "very_stable",
    }
    await client.post("/api/v1/profile/assessment", headers=headers_a, json=submission)

    # User B should NOT see User A's profile
    user_b_id = str(uuid.uuid4())
    token_b = create_access_token(user_id=user_b_id, email=f"userb_{uuid.uuid4().hex[:8]}@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    res_b = await client.get("/api/v1/profile", headers=headers_b)
    assert res_b.status_code == 404


@pytest.mark.asyncio
async def test_goals_crud_and_isolation(client: AsyncClient):
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id=user_id, email=f"goals_{uuid.uuid4().hex[:8]}@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Goal
    create_payload = {
        "name": "House Downpayment",
        "type": "real_estate",
        "target_amount": "80000.00",
        "target_date": "2029-12-31",
        "priority": 1,
    }
    create_res = await client.post("/api/v1/goals", headers=headers, json=create_payload)
    assert create_res.status_code == 201
    goal = create_res.json()
    assert goal["name"] == "House Downpayment"
    assert goal["priority"] == 1
    goal_id = goal["id"]

    # 2. List Goals
    list_res = await client.get("/api/v1/goals", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Update Goal
    update_res = await client.put(
        f"/api/v1/goals/{goal_id}",
        headers=headers,
        json={"target_amount": "90000.00", "priority": 2}
    )
    assert update_res.status_code == 200
    assert update_res.json()["target_amount"] == "90000.00"
    assert update_res.json()["priority"] == 2

    # 4. User B cannot access or modify User A's goal
    user_b_id = str(uuid.uuid4())
    token_b = create_access_token(user_id=user_b_id, email=f"other_{uuid.uuid4().hex[:8]}@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    other_update = await client.put(
        f"/api/v1/goals/{goal_id}",
        headers=headers_b,
        json={"name": "Hacked Name"}
    )
    assert other_update.status_code == 404

    # 5. Delete Goal
    del_res = await client.delete(f"/api/v1/goals/{goal_id}", headers=headers)
    assert del_res.status_code == 204

    # Confirm deleted
    list_res2 = await client.get("/api/v1/goals", headers=headers)
    goal_ids = [g["id"] for g in list_res2.json()]
    assert goal_id not in goal_ids
