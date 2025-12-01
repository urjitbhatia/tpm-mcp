"""Pydantic models for project tracking."""
import json
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class FeatureStatus(str, Enum):
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
    repo_path: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class ProjectCreate(BaseModel):
    org_id: str
    name: str
    repo_path: Optional[str] = None
    description: Optional[str] = None


class Feature(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    status: FeatureStatus = FeatureStatus.BACKLOG
    priority: Priority = Priority.MEDIUM
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Rich metadata fields
    assignees: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    related_repos: Optional[list[str]] = None
    acceptance_criteria: Optional[list[str]] = None
    blockers: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None  # All other rich data


class FeatureCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    status: FeatureStatus = FeatureStatus.BACKLOG
    priority: Priority = Priority.MEDIUM
    assignees: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    related_repos: Optional[list[str]] = None
    acceptance_criteria: Optional[list[str]] = None
    blockers: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[FeatureStatus] = None
    priority: Optional[Priority] = None
    assignees: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    related_repos: Optional[list[str]] = None
    acceptance_criteria: Optional[list[str]] = None
    blockers: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class Task(BaseModel):
    id: str
    feature_id: str
    title: str
    details: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    complexity: Complexity = Complexity.MEDIUM
    created_at: datetime
    completed_at: Optional[datetime] = None
    # Rich metadata fields
    acceptance_criteria: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None  # files_created, files_modified, test_results, etc.


class TaskCreate(BaseModel):
    feature_id: str
    title: str
    details: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    complexity: Complexity = Complexity.MEDIUM
    acceptance_criteria: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    complexity: Optional[Complexity] = None
    acceptance_criteria: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


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


class FeatureView(BaseModel):
    id: str
    title: str
    status: FeatureStatus
    priority: Priority
    tags: Optional[list[str]] = None
    task_count: int = 0
    tasks_done: int = 0
    tasks: list[TaskView] = Field(default_factory=list)


class ProjectView(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    feature_count: int = 0
    features_done: int = 0
    features: list[FeatureView] = Field(default_factory=list)


class OrgView(BaseModel):
    id: str
    name: str
    projects: list[ProjectView] = Field(default_factory=list)


class RoadmapView(BaseModel):
    """Full roadmap at a glance."""
    orgs: list[OrgView] = Field(default_factory=list)
    stats: dict = Field(default_factory=dict)


# Helper functions for JSON serialization
def to_json_str(value: Any) -> Optional[str]:
    """Convert a value to JSON string for storage."""
    if value is None:
        return None
    return json.dumps(value)


def from_json_str(value: Optional[str]) -> Any:
    """Parse a JSON string from storage."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None
