import uuid
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_user_signup_and_login_flow(client: AsyncClient):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "SuperSecurePassword123!"
    name = "Test Investor"

    # 1. Sign up
    signup_res = await client.post(
        "/api/v1/auth/signup",
        json={"email": unique_email, "password": password, "name": name}
    )
    assert signup_res.status_code == 201
    signup_data = signup_res.json()
    assert "access_token" in signup_data
    assert "refresh_token" in signup_data
    assert signup_data["user"]["email"] == unique_email
    assert signup_data["user"]["name"] == name
    assert signup_data["user"]["is_admin"] is False

    # 2. Duplicate signup fails
    dup_res = await client.post(
        "/api/v1/auth/signup",
        json={"email": unique_email, "password": password, "name": name}
    )
    assert dup_res.status_code == 409

    # 3. Login with correct credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password}
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 4. Login with invalid password fails
    bad_login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"}
    )
    assert bad_login_res.status_code == 401

    # 5. Access protected /me without token fails
    unauth_me = await client.get("/api/v1/auth/me")
    assert unauth_me.status_code == 401

    # 6. Access protected /me with malformed token fails
    malformed_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"}
    )
    assert malformed_me.status_code == 401

    # 7. Access protected /me with valid token succeeds
    auth_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert auth_me.status_code == 200
    me_data = auth_me.json()
    assert me_data["email"] == unique_email
    assert me_data["name"] == name

    # 8. Update user profile
    update_res = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "Updated Investor Name"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Investor Name"

    # 9. Refresh token
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()

    # 10. Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_admin_authorization_boundary(client: AsyncClient):
    # Regular user token
    reg_user_id = str(uuid.uuid4())
    reg_token = create_access_token(
        user_id=reg_user_id,
        email="regular@example.com",
        is_admin=False
    )

    # Regular user accessing admin endpoint gets 403 Forbidden
    res_reg = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {reg_token}"}
    )
    assert res_reg.status_code == 403
    assert res_reg.json()["detail"] == "Administrator access required"

    # Admin user token
    admin_id = str(uuid.uuid4())
    admin_token = create_access_token(
        user_id=admin_id,
        email="admin@example.com",
        is_admin=True
    )

    # Admin user accessing admin endpoint succeeds
    res_admin = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    assert isinstance(res_admin.json(), list)


@pytest.mark.asyncio
async def test_password_reset_request(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/reset-password",
        json={"email": "anyuser@example.com"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
