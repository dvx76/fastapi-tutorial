import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Recreate app for every test to start with clean database."""
    import importlib

    import main

    importlib.reload(main)

    from main import app

    return TestClient(app)


@pytest.mark.parametrize("priority", [1, 2, 3, 4, 5])
def test_post_task_all_priorities(client: TestClient, priority: int):
    response = client.post(
        "/tasks",
        json={
            "title": "abc",
            "description": "test description",
            "priority": priority,
        },
    )
    assert response.status_code == 201
    assert response.json() == {
        "title": "abc",
        "description": "test description",
        "priority": priority,
        "id": 1,
    }


def test_post_task_no_description_and_id_increments(client: TestClient):
    response_1 = client.post("/tasks", json={"title": "title 1", "priority": 1})
    response_2 = client.post("/tasks", json={"title": "title 2", "priority": 1})
    assert response_2.status_code == 201
    assert response_1.json()["id"] == 1
    assert response_2.json()["id"] == 2


@pytest.mark.parametrize(
    "title, priority",
    [("", 1), ("te", 1), ("test", -1), ("test", 0), ("test", 6), ("test", "a")],
)
def test_post_task_validation_errors(client: TestClient, title: str, priority: int):
    response = client.post(
        "/tasks",
        json={
            "title": title,
            "priority": priority,
        },
    )
    assert response.status_code == 422


def test_get_task_succeess(client: TestClient):
    post_input = {
        "title": "test title",
        "description": "test description",
        "priority": 1,
    }
    client.post("/tasks", json=post_input)
    response = client.get("/tasks/1")
    assert response.status_code == 200
    expected_response = post_input | {"id": 1}
    assert response.json() == expected_response


def test_get_task_not_found(client: TestClient):
    response = client.get("/tasks/1")
    assert response.status_code == 404
    assert response.json()


def test_get_all_tasks_filtered(client: TestClient):
    for post in range(1, 4):
        client.post(
            "/tasks",
            json={
                "title": f"test title {post}",
                "description": f"test description {post}",
                "priority": post,
            },
        )

    # All tasks
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Only 2 tasks with priority >= 2
    response = client.get("/tasks", params={"min_priority": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Only 1 task with priority >= 2 and 'title 2' in title
    response = client.get("/tasks", params={"min_priority": 2, "q": "title 2"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Test min_priority read from cookies
    response = client.get("/tasks", cookies={"min_priority": "3"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Test query param overrides preference from cookies
    response = client.get(
        "/tasks", params={"min_priority": 2}, cookies={"min_priority": "3"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_patch_task(client: TestClient):
    client.post(
        "/tasks",
        json={
            "title": "test title",
            "description": "test description",
            "priority": 3,
        },
    )
    response = client.patch("/tasks/1", json={"description": "updated"})
    assert response.status_code == 200
    assert response.json() == {
        "title": "test title",
        "description": "updated",
        "priority": 3,
        "id": 1,
    }


def test_patch_task_found(client: TestClient):
    response = client.patch("/tasks/1", json={"description": "updated"})
    assert response.status_code == 404


def test_preferences_set(client: TestClient):
    response = client.post("/preferences", json={"min_priority": 3})
    assert response.status_code == 204
    assert response.cookies == {"min_priority": "3"}
