"""
Tests for: email verification, password reset, and the verified-email guard on lists.
"""
import pytest
from datetime import datetime, timedelta
from hashlib import sha256
from unittest.mock import patch
import secrets


# ── Email verification — request ──────────────────────────────────────────────

async def test_request_verification_sends_email(client, registered_user):
    with patch("app.routes.verification.send_email_verification") as mock_send:
        resp = await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
    assert resp.status_code == 204
    mock_send.assert_called_once()
    assert mock_send.call_args[0][0] == registered_user["email"]


async def test_request_verification_noop_when_already_verified(client, verified_user):
    with patch("app.routes.verification.send_email_verification") as mock_send:
        resp = await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {verified_user['token']}"},
        )
    assert resp.status_code == 204
    mock_send.assert_not_called()


async def test_request_verification_cooldown_blocks_resend(client, registered_user, db):
    """Second request within 60 s is silently ignored — no new token created."""
    with patch("app.routes.verification.send_email_verification"):
        await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
    token_count_after_first = await db["email_verifications"].count_documents({})

    with patch("app.routes.verification.send_email_verification") as mock_send:
        resp = await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
    assert resp.status_code == 204
    mock_send.assert_not_called()
    assert await db["email_verifications"].count_documents({}) == token_count_after_first


async def test_request_verification_invalidates_previous_token(client, registered_user, db):
    """Re-requesting after the cooldown creates a new token and marks old one used."""
    with patch("app.routes.verification.send_email_verification"):
        await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )

    # Simulate time passing past the cooldown window
    await db["email_verifications"].update_many(
        {}, {"$set": {"created_at": datetime.utcnow() - timedelta(seconds=61)}}
    )

    with patch("app.routes.verification.send_email_verification") as mock_send:
        resp = await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
    assert resp.status_code == 204
    mock_send.assert_called_once()

    # Only the new token should be unused
    unused = await db["email_verifications"].count_documents({"used_at": None})
    assert unused == 1


# ── Email verification — verify ───────────────────────────────────────────────

async def test_verify_email_success(client, registered_user):
    with patch("app.routes.verification.send_email_verification") as mock_send:
        await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        raw_token = mock_send.call_args[0][1]

    resp = await client.post("/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 204

    me = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert me.json()["email_verified"] is True


async def test_verify_email_invalid_token(client):
    resp = await client.post("/v1/auth/verify-email", json={"token": "x" * 32})
    assert resp.status_code == 400


async def test_verify_email_reuse_rejected(client, registered_user):
    """Using the same token a second time must return 400."""
    with patch("app.routes.verification.send_email_verification") as mock_send:
        await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        raw_token = mock_send.call_args[0][1]

    await client.post("/v1/auth/verify-email", json={"token": raw_token})
    resp = await client.post("/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 400


async def test_verify_email_expired_token(client, registered_user, db):
    """Manually insert an expired token and confirm it is rejected."""
    raw = secrets.token_urlsafe(32)
    token_hash = sha256(raw.encode()).hexdigest()
    await db["email_verifications"].insert_one({
        "user_id": registered_user["user"]["_id"],
        "email": registered_user["email"],
        "token_hash": token_hash,
        "created_at": datetime.utcnow() - timedelta(hours=25),
        "expires_at": datetime.utcnow() - timedelta(hours=1),
        "used_at": None,
    })
    resp = await client.post("/v1/auth/verify-email", json={"token": raw})
    assert resp.status_code == 400


# ── Password reset ────────────────────────────────────────────────────────────

async def test_forgot_password_sends_email(client, registered_user):
    with patch("app.routes.verification.send_password_reset") as mock_send:
        resp = await client.post(
            "/v1/auth/forgot-password",
            json={"email": registered_user["email"]},
        )
    assert resp.status_code == 204
    mock_send.assert_called_once()


async def test_forgot_password_unknown_email_still_204(client):
    """Anti-enumeration: always 204 even if email not registered."""
    with patch("app.routes.verification.send_password_reset") as mock_send:
        resp = await client.post(
            "/v1/auth/forgot-password",
            json={"email": "ghost@example.com"},
        )
    assert resp.status_code == 204
    mock_send.assert_not_called()


async def test_reset_password_success(client, registered_user):
    with patch("app.routes.verification.send_password_reset") as mock_send:
        await client.post(
            "/v1/auth/forgot-password",
            json={"email": registered_user["email"]},
        )
        raw_token = mock_send.call_args[0][1]

    resp = await client.post("/v1/auth/reset-password", json={
        "token": raw_token,
        "new_password": "NewPassword2",
    })
    assert resp.status_code == 204

    # Old password no longer works
    old = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": registered_user["password"],
    })
    assert old.status_code == 401

    # New password works
    new = await client.post("/v1/auth/login", data={
        "username": registered_user["email"],
        "password": "NewPassword2",
    })
    assert new.status_code == 200


async def test_reset_password_invalid_token(client):
    resp = await client.post("/v1/auth/reset-password", json={
        "token": "y" * 32,
        "new_password": "NewPassword2",
    })
    assert resp.status_code == 400


async def test_reset_password_token_reuse_rejected(client, registered_user):
    """A reset token can only be used once."""
    with patch("app.routes.verification.send_password_reset") as mock_send:
        await client.post(
            "/v1/auth/forgot-password",
            json={"email": registered_user["email"]},
        )
        raw_token = mock_send.call_args[0][1]

    await client.post("/v1/auth/reset-password", json={
        "token": raw_token, "new_password": "NewPassword2"
    })
    resp = await client.post("/v1/auth/reset-password", json={
        "token": raw_token, "new_password": "NewPassword3"
    })
    assert resp.status_code == 400


async def test_reset_password_weak_no_digit(client):
    resp = await client.post("/v1/auth/reset-password", json={
        "token": "z" * 32,
        "new_password": "NoDigitsHere",
    })
    assert resp.status_code == 422


async def test_reset_password_confirm_mismatch(client):
    resp = await client.post("/v1/auth/reset-password", json={
        "token": "a" * 32,
        "new_password": "NewPassword2",
        "confirm_new_password": "DifferentPass2",
    })
    assert resp.status_code == 422


# ── Email verification guard ──────────────────────────────────────────────────

async def test_create_list_blocked_when_unverified(client, registered_user):
    resp = await client.post(
        "/v1/lists",
        json={"title": "My List"},
        headers={"Authorization": f"Bearer {registered_user['token']}"},
    )
    assert resp.status_code == 403


async def test_create_list_allowed_when_verified(client, verified_user):
    resp = await client.post(
        "/v1/lists",
        json={"title": "My List"},
        headers={"Authorization": f"Bearer {verified_user['token']}"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "My List"
