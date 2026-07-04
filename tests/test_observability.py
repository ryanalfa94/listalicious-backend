import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_basic_stats(client):
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "listalicious-backend"
    assert "requests_total" in body
    assert "status_codes" in body
