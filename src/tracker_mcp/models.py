"""Pydantic models for project tracking."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FeatureStatus(str, Enum):
    BACKLOG = "backlog"
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    DONE = "done"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    DONE = "done"
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


class FeatureCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    status: FeatureStatus = FeatureStatus.BACKLOG
    priority: Priority = Priority.MEDIUM


class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[FeatureStatus] = None
    priority: Optional[Priority] = None


class Task(BaseModel):
    id: str
    feature_id: str
    title: str
    details: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    complexity: Complexity = Complexity.MEDIUM
    created_at: datetime
    completed_at: Optional[datetime] = None


class TaskCreate(BaseModel):
    feature_id: str
    title: str
    details: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    complexity: Complexity = Complexity.MEDIUM


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    details: Optional[str] = None
    status: Optional[TaskStatus] = None
    complexity: Optional[Complexity] = None


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
    complexity: Complexity


class FeatureView(BaseModel):
    id: str
    title: str
    status: FeatureStatus
    priority: Priority
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
