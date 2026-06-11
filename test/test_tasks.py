import pytest 
from httpx import AsyncClient

from test.conftest import auth_header, create_test_user, login_user

@pytest.mark.anyio
async def test_get_tasks_empty(client: AsyncClient):
    response = await client.get("/api/items")

    assert response.status_code == 200
    data = response.json()
    assert data["tasks"] == []
    assert data["total"] == 0
    assert data["has_more"] is False

@pytest.mark.anyio
async def test_get_task_not_found(client: AsyncClient):
    response = await client.get("/api/items/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

@pytest.mark.anyio
async def test_create_test_success(client: AsyncClient):
    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/items",
        json={"title": "My First Post", "content": "This is the content"},
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My First Post"
    assert data["content"] == "This is the content"
    assert data["user_id"] == user["id"]
    assert "id" in data
    assert "created_at" in data
    assert data["user"]["username"] == "testuser"


@pytest.mark.anyio
async def test_create_post_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/items",
        json={"title": "Test Post", "content": "Test content"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.anyio
async def test_update_post_success(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/items",
        json={"title": "Original Title", "content": "Original content"},
        headers=headers,
    )
    item_id = response.json()["id"]

    response = await client.patch(
        f"/api/items/{item_id}",
        json={"title": "Updated Title"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["content"] == "Original content"

@pytest.mark.anyio
async def test_update_post_wrong_user(client: AsyncClient):
    await create_test_user(client, username="user1", email="user1@example.com")
    token1 = await login_user(client, email="user1@example.com")

    response = await client.post(
        "/api/items",
        json={"title": "User 1's Post", "content": "Only user 1 can edit this"},
        headers=auth_header(token1),
    )
    item_id = response.json()["id"]

    await create_test_user(client, username="user2", email="user2@example.com")
    token2 = await login_user(client, email="user2@example.com")

    response = await client.patch(
        f"/api/items/{item_id}",
        json={"title": "Hacked Title"},
        headers=auth_header(token2),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to edit this task"

@pytest.mark.anyio
async def test_get_posts_with_pagination(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    for i in range(5):
        response = await client.post(
            "/api/items",
            json={"title": f"Post {i}", "content": f"Content for post {i}"},
            headers=headers,
        )
        assert response.status_code == 201

    response = await client.get("/api/items")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["tasks"]) == 5
    assert data["has_more"] is False

    response = await client.get("/api/items?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["tasks"]) == 2
    assert data["has_more"] is True

    response = await client.get("/api/items?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["tasks"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2