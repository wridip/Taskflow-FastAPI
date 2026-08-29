import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_workspace(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/workspaces",
        headers=auth_headers,
        json={
            "name": "Acme Corp",
            "slug": "acme-corp",
            "description": "Primary workspace for Acme Corp",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert data["slug"] == "acme-corp"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_workspace_duplicate_slug_fails(client: AsyncClient, auth_headers, test_workspace):
    response = await client.post(
        "/api/v1/workspaces",
        headers=auth_headers,
        json={
            "name": "Engineering Team Duplicate",
            "slug": "engineering-team",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "SLUG_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_list_user_workspaces(client: AsyncClient, auth_headers, test_workspace):
    response = await client.get("/api/v1/workspaces", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(w["slug"] == "engineering-team" for w in data)


@pytest.mark.asyncio
async def test_get_workspace_details(client: AsyncClient, auth_headers, test_workspace):
    response = await client.get(f"/api/v1/workspaces/{test_workspace.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_workspace.id
    assert len(data["members"]) >= 1
    assert data["members"][0]["role"] == "OWNER"


@pytest.mark.asyncio
async def test_add_and_update_workspace_member(
    client: AsyncClient,
    auth_headers,
    test_workspace,
    test_member_user,
):
    # Add member as VIEWER
    add_res = await client.post(
        f"/api/v1/workspaces/{test_workspace.id}/members",
        headers=auth_headers,
        json={
            "email": test_member_user.email,
            "role": "VIEWER",
        },
    )
    assert add_res.status_code == 201
    member_data = add_res.json()
    assert member_data["user_email"] == test_member_user.email
    assert member_data["role"] == "VIEWER"

    # Promote to ADMIN
    update_res = await client.patch(
        f"/api/v1/workspaces/{test_workspace.id}/members/{test_member_user.id}",
        headers=auth_headers,
        json={"role": "ADMIN"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["role"] == "ADMIN"

    # Remove member
    remove_res = await client.delete(
        f"/api/v1/workspaces/{test_workspace.id}/members/{test_member_user.id}",
        headers=auth_headers,
    )
    assert remove_res.status_code == 200
    assert remove_res.json()["success"] is True
