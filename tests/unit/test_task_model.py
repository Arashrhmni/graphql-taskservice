"""
Unit tests for app.models.task (the in-memory store / domain logic).
Run with: pytest tests/unit/
"""

import pytest

from app.models.task import (
    Priority,
    Status,
    Task,
    create,
    delete,
    get_all,
    get_by_id,
    reset_store,
    update,
)


@pytest.fixture(autouse=True)
def clean_store():
    """Isolate each test with an empty store."""
    reset_store()
    yield
    reset_store()


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_returns_task_with_id():
    t = create(title="Test task", description="desc")
    assert t.id
    assert t.title == "Test task"
    assert t.status == Status.TODO
    assert t.priority == Priority.MEDIUM


def test_create_respects_priority():
    t = create("urgent", "now", priority=Priority.HIGH)
    assert t.priority == Priority.HIGH


def test_create_stores_tags():
    t = create("tagged", "desc", tags=["alpha", "beta"])
    assert t.tags == ["alpha", "beta"]


# ---------------------------------------------------------------------------
# get_all / filtering
# ---------------------------------------------------------------------------

def test_get_all_returns_all():
    create("a", "d1")
    create("b", "d2")
    assert len(get_all()) == 2


def test_filter_by_status():
    t = create("a", "d")
    update(t.id, status=Status.DONE)
    create("b", "d2")  # stays TODO
    done = get_all(status=Status.DONE)
    assert len(done) == 1
    assert done[0].id == t.id


def test_filter_by_priority():
    create("hi", "d", priority=Priority.HIGH)
    create("lo", "d", priority=Priority.LOW)
    highs = get_all(priority=Priority.HIGH)
    assert len(highs) == 1
    assert highs[0].title == "hi"


def test_filter_by_tag():
    create("a", "d", tags=["devops"])
    create("b", "d", tags=["backend"])
    results = get_all(tag="devops")
    assert len(results) == 1
    assert results[0].title == "a"


def test_get_all_empty_store():
    assert get_all() == []


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_found():
    t = create("x", "y")
    found = get_by_id(t.id)
    assert found is not None
    assert found.id == t.id


def test_get_by_id_not_found():
    assert get_by_id("nonexistent-id") is None


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def test_update_title():
    t = create("old", "d")
    updated = update(t.id, title="new")
    assert updated.title == "new"


def test_update_status():
    t = create("x", "d")
    updated = update(t.id, status=Status.IN_PROGRESS)
    assert updated.status == Status.IN_PROGRESS


def test_update_tags():
    t = create("x", "d", tags=["a"])
    updated = update(t.id, tags=["b", "c"])
    assert updated.tags == ["b", "c"]


def test_update_nonexistent_returns_none():
    result = update("bad-id", title="x")
    assert result is None


def test_update_bumps_updated_at():
    t = create("x", "d")
    original_ts = t.updated_at
    import time; time.sleep(0.01)
    updated = update(t.id, title="new")
    assert updated.updated_at >= original_ts


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

def test_delete_existing():
    t = create("x", "d")
    assert delete(t.id) is True
    assert get_by_id(t.id) is None


def test_delete_nonexistent():
    assert delete("ghost-id") is False


def test_delete_reduces_count():
    t1 = create("a", "d")
    create("b", "d")
    delete(t1.id)
    assert len(get_all()) == 1
