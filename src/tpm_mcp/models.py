"""Pydantic models for project tracking."""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    BACKLOG = "backlog"
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    COMPLETED = "completed"  # Alias for done (used in existing data)
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    COMPLETED = "completed"  # Alias for done (used in existing data)
    BLOCKED = "blocked"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# Base models
class Org(BaseModel):
    id: str
    name: str
    created_at: datetime


class OrgCreate(BaseModel):
    name: str


class Project(BaseModel):
    id: str
    org_id: str
    name: str
    repo_path: str | None = None
    description: str | None = None
    created_at: datetime


class ProjectCreate(BaseModel):
    org_id: str
    name: str
    repo_path: str | None = None
    description: str | None = None


class Ticket(BaseModel):
    id: str
    project_id: str
    title: str
    description: str | None = None
    status: TicketStatus = TicketStatus.BACKLOG
    priority: Priority = Priority.MEDIUM
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # Rich metadata fields
    assignees: list[str] | None = None
    tags: list[str] | None = None
    related_repos: list[str] | None = None
    acceptance_criteria: list[str] | None = None
    blockers: list[str] | None = None
    metadata: dict[str, Any] | None = None  # All other rich data


class TicketCreate(BaseModel):
    project_id: str
    title: str
    description: str | None = None
    status: TicketStatus = TicketStatus.BACKLOG
    priority: Priority = Priority.MEDIUM
    assignees: list[str] | None = None
    tags: list[str] | None = None
    related_repos: list[str] | None = None
    acceptance_criteria: list[str] | None = None
    blockers: list[str] | None = None
    metadata: dict[str, Any] | None = None


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: Priority | None = None
    assignees: list[str] | None = None
    tags: list[str] | None = None
    related_repos: list[str] | None = None
    acceptance_criteria: list[str] | None = None
    blockers: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Task(BaseModel):
    id: str
    ticket_id: str
    title: str
    details: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    complexity: Complexity = Complexity.MEDIUM
    created_at: datetime
    completed_at: datetime | None = None
    # Rich metadata fields
    acceptance_criteria: list[str] | None = None
    metadata: dict[str, Any] | None = None  # files_created, files_modified, test_results, etc.


class TaskCreate(BaseModel):
    ticket_id: str
    title: str
    details: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    complexity: Complexity = Complexity.MEDIUM
    acceptance_criteria: list[str] | None = None
    metadata: dict[str, Any] | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    details: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    complexity: Complexity | None = None
    acceptance_criteria: list[str] | None = None
    metadata: dict[str, Any] | None = None


class Note(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    content: str
    created_at: datetime


class NoteCreate(BaseModel):
    entity_type: str
    entity_id: str
    content: str


# View models for roadmap display
class TaskView(BaseModel):
    id: str
    title: str
    status: TaskStatus
    priority: Priority = Priority.MEDIUM
    complexity: Complexity = Complexity.MEDIUM


class TicketView(BaseModel):
    id: str
    title: str
    status: TicketStatus
    priority: Priority
    tags: list[str] | None = None
    task_count: int = 0
    tasks_done: int = 0
    tasks: list[TaskView] = Field(default_factory=list)


class ProjectView(BaseModel):
    id: str
    name: str
    description: str | None = None
    ticket_count: int = 0
    tickets_done: int = 0
    tickets: list[TicketView] = Field(default_factory=list)


class OrgView(BaseModel):
    id: str
    name: str
    projects: list[ProjectView] = Field(default_factory=list)


class RoadmapView(BaseModel):
    """Full roadmap at a glance."""

    orgs: list[OrgView] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)


# Helper functions for JSON serialization
def to_json_str(value: Any) -> str | None:
    """Convert a value to JSON string for storage."""
    if value is None:
        return None
    return json.dumps(value)


def from_json_str(value: str | None) -> Any:
    """Parse a JSON string from storage."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
