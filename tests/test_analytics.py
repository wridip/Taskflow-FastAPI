import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_workspace_analytics(client: AsyncClient, auth_headers, test_workspace, test_project, test_user):
    # Create a couple tasks with different statuses and priorities
    await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Task 1", "status": "DONE", "priority": "HIGH", "assignee_id": test_user.id},
    )
    await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Task 2", "status": "TODO", "priority": "MEDIUM", "assignee_id": test_user.id},
    )

    response = await client.get(
        f"/api/v1/workspaces/{test_workspace.id}/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == test_workspace.id
    assert data["total_tasks"] == 2
    assert data["completed_tasks"] == 1
    assert data["completion_rate"] == 50.0
    assert "tasks_by_status" in data
    assert "tasks_by_priority" in data
    assert len(data["member_workloads"]) >= 1


@pytest.mark.asyncio
async def test_workspace_activity_feed(client: AsyncClient, auth_headers, test_workspace, test_project):
    # Create task to generate activity
    await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Audited Task"},
    )

    response = await client.get(
        f"/api/v1/workspaces/{test_workspace.id}/activity",
        headers=auth_headers,
    )
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, list)
    assert len(activities) >= 1
    assert any(a["action"] in ["CREATED", "MEMBER_ADDED"] for a in activities)
