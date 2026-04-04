# ── Step 1: env vars BEFORE any app imports ──────────────────────────────────
import os
os.environ["MONGO_DB_NAME"] = "listalicious_test"
os.environ["ENV"] = "dev"

# ── Step 2: replace Motor with an in-memory mock BEFORE app imports ───────────
# This intercepts the `from motor.motor_asyncio import AsyncIOMotorClient` in
# database.py so that all DB calls go to the in-memory mongomock store.
from mongomock_motor import AsyncMongoMockClient
import motor.motor_asyncio
motor.motor_asyncio.AsyncIOMotorClient = AsyncMongoMockClient

# ── Step 3: now safe to import app ────────────────────────────────────────────
import pytest
import pytest_asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database.database import db as _db
from app.core.limiter import limiter


# ── DB + rate limiter cleanup ─────────────────────────────────────────────────
@pytest_asyncio.fixture(autouse=True)
async def clean_collections():
    """Wipe every collection and reset rate-limit counters after each test."""
    yield
    for col in ["users", "email_verifications", "password_resets",
                "revoked_tokens", "grocery_lists", "items"]:
        await _db[col].delete_many({})
    # Reset in-memory rate-limit counters so tests don't bleed into each other
    limiter._storage.reset()


# ── HTTP client ───────────────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Direct DB access ──────────────────────────────────────────────────────────
@pytest.fixture
def db():
    return _db


# ── Pre-registered (unverified) user ──────────────────────────────────────────
@pytest_asyncio.fixture
async def registered_user(client):
    resp = await client.post("/v1/auth/register", json={
        "email": "user@example.com",
        "password": "Password1",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return {
        "token": data["access_token"],
        "user": data["user"],
        "email": "user@example.com",
        "password": "Password1",
    }


# ── Fully verified user ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def verified_user(client, registered_user):
    """Runs the full email-verification flow and returns the same user dict."""
    with patch("app.routes.verification.send_email_verification") as mock_send:
        resp = await client.post(
            "/v1/auth/request-email-verification",
            headers={"Authorization": f"Bearer {registered_user['token']}"},
        )
        assert resp.status_code == 204, resp.text
        raw_token = mock_send.call_args[0][1]

    resp = await client.post("/v1/auth/verify-email", json={"token": raw_token})
    assert resp.status_code == 204, resp.text
    return registered_user
