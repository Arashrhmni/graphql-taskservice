"""
Domain models for the Task microservice.
Uses a simple in-memory store for portability; swap for a DB adapter in production.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Status(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@dataclass
class Task:
    title: str
    description: str
    priority: Priority = Priority.MEDIUM
    status: Status = Status.TODO
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# In-memory store (thread-safe enough for demo; replace with DB in prod)
# ---------------------------------------------------------------------------
_store: Dict[str, Task] = {}


def seed_store() -> None:
    """Populate the store with demo data."""
    tasks = [
        Task(
            title="Design GraphQL schema",
            description="Define types, queries, and mutations.",
            priority=Priority.HIGH,
            status=Status.DONE,
            tags=["backend", "api"],
        ),
        Task(
            title="Write unit tests",
            description="Cover resolvers and service layer with pytest.",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            tags=["testing"],
        ),
        Task(
            title="Create Dockerfile",
            description="Multi-stage build for a minimal image.",
            priority=Priority.MEDIUM,
            status=Status.TODO,
            tags=["devops"],
        ),
        Task(
            title="Write Kubernetes manifests",
            description="Deployment, Service, and HPA.",
            priority=Priority.MEDIUM,
            status=Status.TODO,
            tags=["devops", "k8s"],
        ),
    ]
    for t in tasks:
        _store[t.id] = t


seed_store()


def get_all(
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
    tag: Optional[str] = None,
) -> List[Task]:
    results = list(_store.values())
    if status:
        results = [t for t in results if t.status == status]
    if priority:
        results = [t for t in results if t.priority == priority]
    if tag:
        results = [t for t in results if tag in t.tags]
    return sorted(results, key=lambda t: t.created_at)


def get_by_id(task_id: str) -> Optional[Task]:
    return _store.get(task_id)


def create(
    title: str,
    description: str,
    priority: Priority = Priority.MEDIUM,
    tags: Optional[List[str]] = None,
) -> Task:
    task = Task(title=title, description=description, priority=priority, tags=tags or [])
    _store[task.id] = task
    return task


def update(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[Priority] = None,
    status: Optional[Status] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Task]:
    task = _store.get(task_id)
    if not task:
        return None
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if priority is not None:
        task.priority = priority
    if status is not None:
        task.status = status
    if tags is not None:
        task.tags = tags
    task.updated_at = datetime.now(timezone.utc)
    return task


def delete(task_id: str) -> bool:
    if task_id in _store:
        del _store[task_id]
        return True
    return False


def reset_store(initial: Optional[List[Task]] = None) -> None:
    """Reset store — used in tests."""
    _store.clear()
    if initial:
        for t in initial:
            _store[t.id] = t
