"""Unit tests for the GraphQL schema layer."""

import pytest

from app.graphql.schema import schema
from app.models.task import reset_store


@pytest.fixture(autouse=True)
def clean():
    reset_store([])
    yield
    reset_store([])


def gql(query: str, variables: dict | None = None):
    result = schema.execute_sync(query, variable_values=variables or {})
    assert result.errors is None, result.errors
    return result.data


CREATE_TASK = """
mutation CreateTask($input: CreateTaskInput!) {
  createTask(input: $input) {
    id title description priority status tags
  }
}
"""

UPDATE_TASK = """
mutation UpdateTask($input: UpdateTaskInput!) {
  updateTask(input: $input) {
    id title status priority tags
  }
}
"""

DELETE_TASK = """
mutation DeleteTask($id: String!) {
  deleteTask(id: $id) { success message }
}
"""

GET_TASKS = """
query GetTasks($status: Status, $priority: Priority, $tag: String) {
  tasks(status: $status, priority: $priority, tag: $tag) {
    id title priority status tags
  }
}
"""

GET_TASK = """
query GetTask($id: String!) {
  task(id: $id) { id title }
}
"""


def test_create_task_basic():
    data = gql(CREATE_TASK, {"input": {"title": "My Task", "description": "Details"}})
    task = data["createTask"]
    assert task["title"] == "My Task"
    assert task["status"] == "TODO"
    assert task["priority"] == "MEDIUM"
    assert task["id"]


def test_create_task_with_tags_and_priority():
    data = gql(
        CREATE_TASK,
        {"input": {"title": "Tagged", "description": "d", "priority": "HIGH", "tags": ["api", "k8s"]}},
    )
    task = data["createTask"]
    assert task["priority"] == "HIGH"
    assert task["tags"] == ["api", "k8s"]


def test_tasks_returns_all():
    gql(CREATE_TASK, {"input": {"title": "A", "description": "d"}})
    gql(CREATE_TASK, {"input": {"title": "B", "description": "d"}})
    data = gql(GET_TASKS)
    assert len(data["tasks"]) == 2


def test_tasks_filter_by_status():
    created = gql(CREATE_TASK, {"input": {"title": "A", "description": "d"}})
    task_id = created["createTask"]["id"]
    gql(UPDATE_TASK, {"input": {"id": task_id, "status": "DONE"}})
    gql(CREATE_TASK, {"input": {"title": "B", "description": "d"}})

    done = gql(GET_TASKS, {"status": "DONE"})
    assert len(done["tasks"]) == 1
    assert done["tasks"][0]["id"] == task_id


def test_tasks_filter_by_tag():
    gql(CREATE_TASK, {"input": {"title": "A", "description": "d", "tags": ["devops"]}})
    gql(CREATE_TASK, {"input": {"title": "B", "description": "d", "tags": ["backend"]}})
    result = gql(GET_TASKS, {"tag": "devops"})
    assert len(result["tasks"]) == 1
    assert result["tasks"][0]["title"] == "A"


def test_get_task_found():
    created = gql(CREATE_TASK, {"input": {"title": "Find me", "description": "d"}})
    task_id = created["createTask"]["id"]
    data = gql(GET_TASK, {"id": task_id})
    assert data["task"]["title"] == "Find me"


def test_get_task_not_found():
    result = schema.execute_sync(GET_TASK, variable_values={"id": "ghost"})
    assert result.errors is None
    assert result.data["task"] is None


def test_update_task_status():
    created = gql(CREATE_TASK, {"input": {"title": "T", "description": "d"}})
    task_id = created["createTask"]["id"]
    data = gql(UPDATE_TASK, {"input": {"id": task_id, "status": "IN_PROGRESS"}})
    assert data["updateTask"]["status"] == "IN_PROGRESS"


def test_update_task_tags():
    created = gql(CREATE_TASK, {"input": {"title": "T", "description": "d", "tags": ["old"]}})
    task_id = created["createTask"]["id"]
    data = gql(UPDATE_TASK, {"input": {"id": task_id, "tags": ["new1", "new2"]}})
    assert data["updateTask"]["tags"] == ["new1", "new2"]


def test_update_nonexistent_task():
    result = schema.execute_sync(UPDATE_TASK, variable_values={"input": {"id": "bad"}})
    assert result.errors is None
    assert result.data["updateTask"] is None


def test_delete_existing_task():
    created = gql(CREATE_TASK, {"input": {"title": "To Delete", "description": "d"}})
    task_id = created["createTask"]["id"]
    data = gql(DELETE_TASK, {"id": task_id})
    assert data["deleteTask"]["success"] is True
    data2 = gql(GET_TASK, {"id": task_id})
    assert data2["task"] is None


def test_delete_nonexistent_task():
    data = gql(DELETE_TASK, {"id": "ghost-id"})
    assert data["deleteTask"]["success"] is False
    assert "not found" in data["deleteTask"]["message"]
