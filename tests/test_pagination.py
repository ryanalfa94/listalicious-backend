async def test_lists_endpoint_returns_pagination_headers(client, verified_user):
    for idx in range(3):
        resp = await client.post(
            "/v1/lists",
            json={"title": f"List {idx}"},
            headers={"Authorization": f"Bearer {verified_user['token']}"},
        )
        assert resp.status_code == 201

    resp = await client.get(
        "/v1/lists?skip=1&limit=1",
        headers={"Authorization": f"Bearer {verified_user['token']}"},
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total-Count"] == "3"
    assert resp.headers["X-Has-More"] == "true"
    assert resp.headers["X-Limit"] == "1"
    assert resp.headers["X-Skip"] == "1"


async def test_items_endpoint_returns_pagination_headers(client, verified_user):
    list_resp = await client.post(
        "/v1/lists",
        json={"title": "Items list"},
        headers={"Authorization": f"Bearer {verified_user['token']}"},
    )
    assert list_resp.status_code == 201
    list_id = list_resp.json()["_id"]

    for idx in range(3):
        item_resp = await client.post(
            f"/v1/lists/{list_id}/items",
            json={"name": f"Item {idx}", "quantity": 1},
            headers={"Authorization": f"Bearer {verified_user['token']}"},
        )
        assert item_resp.status_code == 201

    resp = await client.get(
        f"/v1/lists/{list_id}/items?skip=1&limit=1",
        headers={"Authorization": f"Bearer {verified_user['token']}"},
    )
    assert resp.status_code == 200
    assert resp.headers["X-Total-Count"] == "3"
    assert resp.headers["X-Has-More"] == "true"
    assert resp.headers["X-Limit"] == "1"
    assert resp.headers["X-Skip"] == "1"
