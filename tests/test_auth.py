"""
Tests for: register, login, /me, PATCH /me, account lockout.
"""
import pytest
from app.services.auth_service import MAX_FAILED_LOGINS


# ── Registration ──────────────────────────────────────────────────────────────

async def test_register_success(client):
    resp = await client.post("/v1/auth/register", json={
        "email": "new@example.com",
        "password": "Password1",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email_verified"] is False


async def test_register_password_no_digit(client):
    resp = await client.post("/v1/auth/register", json={
        "email": "a@example.com",
        "password": "NoDigitsHere",
    })
    assert resp.status_code == 422


async def test_register_password_no_letter(client):
    resp = await client.post("/v1/auth/register", json={
        "email": "a@example.com",
        "password": "12345678",
    })
    assert resp.status_code == 422


async def test_register_password_too_short(client):
    resp = await client.post("/v1/auth/register", json={
        "email": "a@example.com",
        "password": "Ab1",
    })
    assert resp.status_code == 422


async def test_register_duplicate_email(client, registered_user):
    resp = await client.post("/v1/auth/register", json={
        "email": registered_user["email"],
        "password": "Password1",
    })
    assert resp.status_code == 400


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client, registered_user):
    resp = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client, registered_user):
    resp = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": "WrongPassword1",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post("/v1/auth/login", data={
        "username": "nobody@example.com",
        "password": "Password1",
    })
    assert resp.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────

async def test_get_me(client, registered_user):
    resp = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == registered_user["email"]
    assert data["email_verified"] is False


async def test_get_me_no_token(client):
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 403


async def test_patch_me_username(client, registered_user):
    resp = await client.patch(
        "/v1/auth/me",
        json={"username": "mynewname"},
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "mynewname"


async def test_patch_me_empty_body(client, registered_user):
    resp = await client.patch(
        "/v1/auth/me",
        json={},
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert resp.status_code == 400


async def test_patch_me_unknown_field_rejected(client, registered_user):
    resp = await client.patch(
        "/v1/auth/me",
        json={"hacked_field": "value"},
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert resp.status_code == 422


# ── Account lockout ───────────────────────────────────────────────────────────

async def test_account_lockout(client, registered_user, db):
    # Set failed count to MAX-1 directly — avoids running 9 real bcrypt ops.
    await db["users"].update_one(
        {"email": registered_user["email"]},
        {"$set": {"failed_login_count": MAX_FAILED_LOGINS - 1}},
    )

    # The MAX-th bad attempt: still returns 401 but sets locked_until.
    resp = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": "BadPassword1",
    })
    assert resp.status_code == 401

    # Next attempt: account is now locked.
    resp = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": "BadPassword1",
    })
    assert resp.status_code == 429


async def test_lockout_resets_on_successful_login(client, registered_user, db):
    await db["users"].update_one(
        {"email": registered_user["email"]},
        {"$set": {"failed_login_count": 5}},
    )

    resp = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200

    user = await db["users"].find_one({"email": registered_user["email"]})
    assert user["failed_login_count"] == 0
    assert user.get("locked_until") is None
