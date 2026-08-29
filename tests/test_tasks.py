import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_task(client: AsyncClient, auth_headers, test_project, test_user):
    create_res = await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={
            "title": "Implement JWT Authentication",
            "description": "Add access and refresh token flows",
            "status": "TODO",
            "priority": "HIGH",
            "estimated_hours": 4.5,
            "assignee_id": test_user.id,
            "tags": "security,auth,backend",
        },
    )
    assert create_res.status_code == 201
    task = create_res.json()
    assert task["title"] == "Implement JWT Authentication"
    assert task["priority"] == "HIGH"
    assert task["assignee_id"] == test_user.id

    # Get task by ID
    get_res = await client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == task["title"]


@pytest.mark.asyncio
async def test_filter_and_search_tasks(client: AsyncClient, auth_headers, test_project):
    # Create multiple tasks
    await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Fix login bug", "status": "TODO", "priority": "URGENT"},
    )
    await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Write documentation", "status": "DONE", "priority": "LOW"},
    )

    # Filter by status
    status_res = await client.get(
        f"/api/v1/projects/{test_project.id}/tasks?status=DONE",
        headers=auth_headers,
    )
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert len(status_data["items"]) == 1
    assert status_data["items"][0]["title"] == "Write documentation"

    # Search keyword
    search_res = await client.get(
        f"/api/v1/projects/{test_project.id}/tasks?search=bug",
        headers=auth_headers,
    )
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["items"]) == 1
    assert search_data["items"][0]["title"] == "Fix login bug"


@pytest.mark.asyncio
async def test_update_task_status(client: AsyncClient, auth_headers, test_project):
    create_res = await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Test Task", "status": "TODO"},
    )
    task_id = create_res.json()["id"]

    status_res = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        headers=auth_headers,
        json={"status": "IN_PROGRESS"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_comments_on_task(client: AsyncClient, auth_headers, test_project):
    create_res = await client.post(
        f"/api/v1/projects/{test_project.id}/tasks",
        headers=auth_headers,
        json={"title": "Task for comment testing"},
    )
    task_id = create_res.json()["id"]

    # Add comment
    add_c_res = await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        headers=auth_headers,
        json={"content": "Looks good! Ready for QA."},
    )
    assert add_c_res.status_code == 201
    assert add_c_res.json()["content"] == "Looks good! Ready for QA."

    # List comments
    list_c_res = await client.get(
        f"/api/v1/tasks/{task_id}/comments",
        headers=auth_headers,
    )
    assert list_c_res.status_code == 200
    comments = list_c_res.json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Looks good! Ready for QA."
