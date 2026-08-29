import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_in_workspace(client: AsyncClient, auth_headers, test_workspace):
    response = await client.post(
        f"/api/v1/workspaces/{test_workspace.id}/projects",
        headers=auth_headers,
        json={
            "name": "Mobile Application",
            "description": "Flutter iOS and Android app",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Mobile Application"
    assert data["workspace_id"] == test_workspace.id
    assert data["is_archived"] is False


@pytest.mark.asyncio
async def test_list_projects_in_workspace(client: AsyncClient, auth_headers, test_workspace, test_project):
    response = await client.get(
        f"/api/v1/workspaces/{test_workspace.id}/projects",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(p["id"] == test_project.id for p in data)


@pytest.mark.asyncio
async def test_get_and_update_project(client: AsyncClient, auth_headers, test_project):
    # Get project
    get_res = await client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == test_project.name

    # Update project
    patch_res = await client.patch(
        f"/api/v1/projects/{test_project.id}",
        headers=auth_headers,
        json={
            "name": "Renamed Project",
            "is_archived": True,
        },
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["name"] == "Renamed Project"
    assert updated_data["is_archived"] is True
