async def test_health_endpoint_reports_database_connection(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["db"] == "connected"


async def test_ready_endpoint_reports_service_readiness(client):
    resp = await client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["service"] == "listalicious-backend"


async def test_api_docs_are_available(client):
    docs_resp = await client.get("/docs")
    assert docs_resp.status_code == 200
    assert "swagger" in docs_resp.text.lower()

    openapi_resp = await client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    assert openapi_resp.json()["info"]["title"] == "Listalicious API"
