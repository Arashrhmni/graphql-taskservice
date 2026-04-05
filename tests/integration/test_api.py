"""Integration tests: full HTTP round-trip through FastAPI + GraphQL."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.task import reset_store


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clean():
    reset_store([])
    yield
    reset_store([])


ENDPOINT = "/graphql"


def post(client, query: str, variables: dict | None = None):
    response = client.post(ENDPOINT, json={"query": query, "variables": variables or {}})
    assert response.status_code == 200, response.text
    body = response.json()
    assert "errors" not in body or body["errors"] is None, body.get("errors")
    return body["data"]


CREATE = """
mutation C($input: CreateTaskInput!) {
  createTask(input: $input) { id title status priority tags }
}
"""

LIST = """
query L($status: Status, $tag: String) {
  tasks(status: $status, tag: $tag) { id title status }
}
"""

UPDATE = """
mutation U($input: UpdateTaskInput!) {
  updateTask(input: $input) { id status title }
}
"""

DELETE = """
mutation D($id: String!) {
  deleteTask(id: $id) { success message }
}
"""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list(client):
    post(client, CREATE, {"input": {"title": "Integration Task", "description": "test"}})
    data = post(client, LIST)
    assert any(task["title"] == "Integration Task" for task in data["tasks"])


def test_create_update_delete(client):
    created = post(client, CREATE, {"input": {"title": "Flow", "description": "d"}})
    task_id = created["createTask"]["id"]

    updated = post(client, UPDATE, {"input": {"id": task_id, "status": "IN_PROGRESS"}})
    assert updated["updateTask"]["status"] == "IN_PROGRESS"

    in_progress = post(client, LIST, {"status": "IN_PROGRESS"})
    assert any(task["id"] == task_id for task in in_progress["tasks"])

    deleted = post(client, DELETE, {"id": task_id})
    assert deleted["deleteTask"]["success"] is True

    remaining = post(client, LIST)
    assert not any(task["id"] == task_id for task in remaining["tasks"])


def test_graphiql_accessible(client):
    response = client.get(ENDPOINT, headers={"Accept": "text/html"})
    assert response.status_code == 200


def test_filter_by_tag(client):
    post(client, CREATE, {"input": {"title": "A", "description": "d", "tags": ["k8s"]}})
    post(client, CREATE, {"input": {"title": "B", "description": "d", "tags": ["api"]}})
    result = post(client, LIST, {"tag": "k8s"})
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["title"] == "A"


def test_multiple_tasks_ordering(client):
    for index in range(5):
        post(client, CREATE, {"input": {"title": f"Task {index}", "description": "d"}})
    result = post(client, LIST)
    assert len(result["tasks"]) == 5


def test_delete_nonexistent(client):
    result = post(client, DELETE, {"id": "does-not-exist"})
    assert result["deleteTask"]["success"] is False
