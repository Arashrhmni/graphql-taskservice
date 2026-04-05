"""Strawberry GraphQL schema: types, queries, and mutations."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

import strawberry

from app.models import task as task_store
from app.models.task import Priority as DomainPriority
from app.models.task import Status as DomainStatus


@strawberry.enum
class Priority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@strawberry.enum
class Status(Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


@strawberry.type
class Task:
    id: str
    title: str
    description: str
    priority: Priority
    status: Status
    tags: List[str]
    created_at: datetime
    updated_at: datetime


@strawberry.type
class DeleteResult:
    success: bool
    message: str


@strawberry.input
class CreateTaskInput:
    title: str
    description: str
    priority: Optional[Priority] = Priority.MEDIUM
    tags: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateTaskInput:
    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    tags: Optional[List[str]] = None


def _to_gql(task: task_store.Task) -> Task:
    return Task(
        id=task.id,
        title=task.title,
        description=task.description,
        priority=Priority(task.priority.value),
        status=Status(task.status.value),
        tags=list(task.tags),
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@strawberry.type
class Query:
    @strawberry.field
    def tasks(
        self,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        tag: Optional[str] = None,
    ) -> List[Task]:
        domain_status = DomainStatus(status.value) if status else None
        domain_priority = DomainPriority(priority.value) if priority else None
        return [_to_gql(task) for task in task_store.get_all(domain_status, domain_priority, tag)]

    @strawberry.field
    def task(self, id: str) -> Optional[Task]:
        task = task_store.get_by_id(id)
        return _to_gql(task) if task else None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_task(self, input: CreateTaskInput) -> Task:
        task = task_store.create(
            title=input.title,
            description=input.description,
            priority=DomainPriority(input.priority.value),
            tags=input.tags,
        )
        return _to_gql(task)

    @strawberry.mutation
    def update_task(self, input: UpdateTaskInput) -> Optional[Task]:
        priority = DomainPriority(input.priority.value) if input.priority else None
        status = DomainStatus(input.status.value) if input.status else None
        task = task_store.update(
            task_id=input.id,
            title=input.title,
            description=input.description,
            priority=priority,
            status=status,
            tags=input.tags,
        )
        return _to_gql(task) if task else None

    @strawberry.mutation
    def delete_task(self, id: str) -> DeleteResult:
        deleted = task_store.delete(id)
        return DeleteResult(
            success=deleted,
            message="Task deleted." if deleted else f"Task {id} not found.",
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
