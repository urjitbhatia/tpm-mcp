"""SQLite database operations for project tracking."""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import (
    Org, OrgCreate,
    Project, ProjectCreate,
    Feature, FeatureCreate, FeatureUpdate, FeatureStatus,
    Task, TaskCreate, TaskUpdate, TaskStatus, Priority, Complexity,
    Note, NoteCreate,
    RoadmapView, OrgView, ProjectView, FeatureView, TaskView,
)

# Default database path
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "tracker-mcp" / "tracker.db"


def get_db_path() -> Path:
    """Get database path, creating parent directories if needed."""
    db_path = Path(DEFAULT_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Initialize database with schema."""
    db_path = db_path or get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        conn.executescript(f.read())

    return conn


def _to_json(value: Any) -> Optional[str]:
    """Convert a value to JSON string for storage."""
    if value is None:
        return None
    return json.dumps(value)


def _from_json(value: Optional[str]) -> Any:
    """Parse a JSON string from storage."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _normalize_feature_status(status: str) -> str:
    """Normalize feature status (completed -> done)."""
    if status == "completed":
        return "done"
    return status


def _normalize_task_status(status: str) -> str:
    """Normalize task status (completed -> done)."""
    if status == "completed":
        return "done"
    return status


class TrackerDB:
    """Database operations for project tracking."""

    def __init__(self, db_path: Optional[Path] = None):
        self.conn = init_db(db_path)

    def _gen_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    # --- Orgs ---

    def create_org(self, data: OrgCreate) -> Org:
        id = self._gen_id()
        now = self._now()
        self.conn.execute(
            "INSERT INTO orgs (id, name, created_at) VALUES (?, ?, ?)",
            (id, data.name, now)
        )
        self.conn.commit()
        return Org(id=id, name=data.name, created_at=datetime.fromisoformat(now))

    def create_org_with_id(self, id: str, name: str, created_at: Optional[str] = None) -> Org:
        """Create org with specific ID (for migration)."""
        now = created_at or self._now()
        self.conn.execute(
            "INSERT OR REPLACE INTO orgs (id, name, created_at) VALUES (?, ?, ?)",
            (id, name, now)
        )
        self.conn.commit()
        return Org(id=id, name=name, created_at=datetime.fromisoformat(now))

    def get_org(self, org_id: str) -> Optional[Org]:
        row = self.conn.execute(
            "SELECT * FROM orgs WHERE id = ?", (org_id,)
        ).fetchone()
        if row:
            return Org(id=row["id"], name=row["name"],
                      created_at=datetime.fromisoformat(row["created_at"]))
        return None

    def list_orgs(self) -> list[Org]:
        rows = self.conn.execute("SELECT * FROM orgs ORDER BY name").fetchall()
        return [Org(id=r["id"], name=r["name"],
                   created_at=datetime.fromisoformat(r["created_at"])) for r in rows]

    # --- Projects ---

    def create_project(self, data: ProjectCreate) -> Project:
        id = self._gen_id()
        now = self._now()
        self.conn.execute(
            """INSERT INTO projects (id, org_id, name, repo_path, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, data.org_id, data.name, data.repo_path, data.description, now)
        )
        self.conn.commit()
        return Project(id=id, org_id=data.org_id, name=data.name,
                      repo_path=data.repo_path, description=data.description,
                      created_at=datetime.fromisoformat(now))

    def create_project_with_id(self, id: str, org_id: str, name: str,
                               repo_path: Optional[str] = None,
                               description: Optional[str] = None,
                               created_at: Optional[str] = None) -> Project:
        """Create project with specific ID (for migration)."""
        now = created_at or self._now()
        self.conn.execute(
            """INSERT OR REPLACE INTO projects (id, org_id, name, repo_path, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, org_id, name, repo_path, description, now)
        )
        self.conn.commit()
        return Project(id=id, org_id=org_id, name=name,
                      repo_path=repo_path, description=description,
                      created_at=datetime.fromisoformat(now))

    def get_project(self, project_id: str) -> Optional[Project]:
        row = self.conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row:
            return Project(
                id=row["id"], org_id=row["org_id"], name=row["name"],
                repo_path=row["repo_path"], description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"])
            )
        return None

    def list_projects(self, org_id: Optional[str] = None) -> list[Project]:
        if org_id:
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE org_id = ? ORDER BY name", (org_id,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
        return [Project(
            id=r["id"], org_id=r["org_id"], name=r["name"],
            repo_path=r["repo_path"], description=r["description"],
            created_at=datetime.fromisoformat(r["created_at"])
        ) for r in rows]

    # --- Features ---

    def create_feature(self, data: FeatureCreate) -> Feature:
        id = f"FEAT-{self._gen_id()}"
        now = self._now()
        self.conn.execute(
            """INSERT INTO features (id, project_id, title, description, status, priority, created_at,
               assignees, tags, related_repos, acceptance_criteria, blockers, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, data.project_id, data.title, data.description,
             data.status.value, data.priority.value, now,
             _to_json(data.assignees), _to_json(data.tags), _to_json(data.related_repos),
             _to_json(data.acceptance_criteria), _to_json(data.blockers), _to_json(data.metadata))
        )
        self.conn.commit()
        return Feature(id=id, project_id=data.project_id, title=data.title,
                      description=data.description, status=data.status,
                      priority=data.priority, created_at=datetime.fromisoformat(now),
                      assignees=data.assignees, tags=data.tags, related_repos=data.related_repos,
                      acceptance_criteria=data.acceptance_criteria, blockers=data.blockers,
                      metadata=data.metadata)

    def create_feature_with_id(self, id: str, project_id: str, title: str,
                               description: Optional[str] = None,
                               status: str = "backlog",
                               priority: str = "medium",
                               created_at: Optional[str] = None,
                               started_at: Optional[str] = None,
                               completed_at: Optional[str] = None,
                               assignees: Optional[list] = None,
                               tags: Optional[list] = None,
                               related_repos: Optional[list] = None,
                               acceptance_criteria: Optional[list] = None,
                               blockers: Optional[list] = None,
                               metadata: Optional[dict] = None) -> Feature:
        """Create feature with specific ID (for migration)."""
        now = created_at or self._now()
        status = _normalize_feature_status(status)
        self.conn.execute(
            """INSERT OR REPLACE INTO features (id, project_id, title, description, status, priority,
               created_at, started_at, completed_at, assignees, tags, related_repos,
               acceptance_criteria, blockers, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, project_id, title, description, status, priority, now, started_at, completed_at,
             _to_json(assignees), _to_json(tags), _to_json(related_repos),
             _to_json(acceptance_criteria), _to_json(blockers), _to_json(metadata))
        )
        self.conn.commit()
        return self.get_feature(id)

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        row = self.conn.execute(
            "SELECT * FROM features WHERE id = ?", (feature_id,)
        ).fetchone()
        if row:
            return self._row_to_feature(row)
        return None

    def _row_to_feature(self, row) -> Feature:
        status = _normalize_feature_status(row["status"])
        return Feature(
            id=row["id"], project_id=row["project_id"], title=row["title"],
            description=row["description"], status=FeatureStatus(status),
            priority=Priority(row["priority"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            assignees=_from_json(row["assignees"]),
            tags=_from_json(row["tags"]),
            related_repos=_from_json(row["related_repos"]),
            acceptance_criteria=_from_json(row["acceptance_criteria"]),
            blockers=_from_json(row["blockers"]),
            metadata=_from_json(row["metadata"]),
        )

    def list_features(self, project_id: Optional[str] = None,
                     status: Optional[FeatureStatus] = None) -> list[Feature]:
        query = "SELECT * FROM features WHERE 1=1"
        params = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY priority, created_at"
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_feature(r) for r in rows]

    def update_feature(self, feature_id: str, data: FeatureUpdate) -> Optional[Feature]:
        updates = []
        params = []
        if data.title is not None:
            updates.append("title = ?")
            params.append(data.title)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status.value)
            if data.status == FeatureStatus.IN_PROGRESS:
                updates.append("started_at = ?")
                params.append(self._now())
            elif data.status in (FeatureStatus.DONE, FeatureStatus.COMPLETED):
                updates.append("completed_at = ?")
                params.append(self._now())
        if data.priority is not None:
            updates.append("priority = ?")
            params.append(data.priority.value)
        if data.assignees is not None:
            updates.append("assignees = ?")
            params.append(_to_json(data.assignees))
        if data.tags is not None:
            updates.append("tags = ?")
            params.append(_to_json(data.tags))
        if data.related_repos is not None:
            updates.append("related_repos = ?")
            params.append(_to_json(data.related_repos))
        if data.acceptance_criteria is not None:
            updates.append("acceptance_criteria = ?")
            params.append(_to_json(data.acceptance_criteria))
        if data.blockers is not None:
            updates.append("blockers = ?")
            params.append(_to_json(data.blockers))
        if data.metadata is not None:
            updates.append("metadata = ?")
            params.append(_to_json(data.metadata))

        if not updates:
            return self.get_feature(feature_id)

        params.append(feature_id)
        self.conn.execute(
            f"UPDATE features SET {', '.join(updates)} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_feature(feature_id)

    # --- Tasks ---

    def create_task(self, data: TaskCreate) -> Task:
        # Get feature to extract prefix
        feature = self.get_feature(data.feature_id)
        if not feature:
            raise ValueError(f"Feature {data.feature_id} not found")

        # Count existing tasks for this feature to generate task number
        count = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE feature_id = ?", (data.feature_id,)
        ).fetchone()[0]

        # Generate task ID like TASK-FEAT-001-1
        feat_num = feature.id.replace("FEAT-", "")
        id = f"TASK-{feat_num}-{count + 1}"
        now = self._now()

        self.conn.execute(
            """INSERT INTO tasks (id, feature_id, title, details, status, priority, complexity,
               created_at, acceptance_criteria, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, data.feature_id, data.title, data.details,
             data.status.value, data.priority.value, data.complexity.value, now,
             _to_json(data.acceptance_criteria), _to_json(data.metadata))
        )
        self.conn.commit()
        return Task(id=id, feature_id=data.feature_id, title=data.title,
                   details=data.details, status=data.status, priority=data.priority,
                   complexity=data.complexity, created_at=datetime.fromisoformat(now),
                   acceptance_criteria=data.acceptance_criteria, metadata=data.metadata)

    def create_task_with_id(self, id: str, feature_id: str, title: str,
                            details: Optional[str] = None,
                            status: str = "pending",
                            priority: str = "medium",
                            complexity: str = "medium",
                            created_at: Optional[str] = None,
                            completed_at: Optional[str] = None,
                            acceptance_criteria: Optional[list] = None,
                            metadata: Optional[dict] = None) -> Task:
        """Create task with specific ID (for migration)."""
        now = created_at or self._now()
        status = _normalize_task_status(status)
        self.conn.execute(
            """INSERT OR REPLACE INTO tasks (id, feature_id, title, details, status, priority, complexity,
               created_at, completed_at, acceptance_criteria, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id, feature_id, title, details, status, priority, complexity, now, completed_at,
             _to_json(acceptance_criteria), _to_json(metadata))
        )
        self.conn.commit()
        return self.get_task(id)

    def get_task(self, task_id: str) -> Optional[Task]:
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row:
            return self._row_to_task(row)
        return None

    def _row_to_task(self, row) -> Task:
        status = _normalize_task_status(row["status"])
        return Task(
            id=row["id"], feature_id=row["feature_id"], title=row["title"],
            details=row["details"], status=TaskStatus(status),
            priority=Priority(row["priority"] or "medium"),
            complexity=Complexity(row["complexity"] or "medium"),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            acceptance_criteria=_from_json(row["acceptance_criteria"]),
            metadata=_from_json(row["metadata"]),
        )

    def list_tasks(self, feature_id: Optional[str] = None,
                  status: Optional[TaskStatus] = None) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if feature_id:
            query += " AND feature_id = ?"
            params.append(feature_id)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at"
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update_task(self, task_id: str, data: TaskUpdate) -> Optional[Task]:
        updates = []
        params = []
        if data.title is not None:
            updates.append("title = ?")
            params.append(data.title)
        if data.details is not None:
            updates.append("details = ?")
            params.append(data.details)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status.value)
            if data.status in (TaskStatus.DONE, TaskStatus.COMPLETED):
                updates.append("completed_at = ?")
                params.append(self._now())
        if data.priority is not None:
            updates.append("priority = ?")
            params.append(data.priority.value)
        if data.complexity is not None:
            updates.append("complexity = ?")
            params.append(data.complexity.value)
        if data.acceptance_criteria is not None:
            updates.append("acceptance_criteria = ?")
            params.append(_to_json(data.acceptance_criteria))
        if data.metadata is not None:
            updates.append("metadata = ?")
            params.append(_to_json(data.metadata))

        if not updates:
            return self.get_task(task_id)

        params.append(task_id)
        self.conn.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_task(task_id)

    # --- Task Dependencies ---

    def add_task_dependency(self, task_id: str, depends_on_id: str) -> bool:
        """Add a dependency between tasks."""
        try:
            self.conn.execute(
                "INSERT INTO task_dependencies (task_id, depends_on_id) VALUES (?, ?)",
                (task_id, depends_on_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_task_dependencies(self, task_id: str) -> list[str]:
        """Get IDs of tasks that this task depends on."""
        rows = self.conn.execute(
            "SELECT depends_on_id FROM task_dependencies WHERE task_id = ?",
            (task_id,)
        ).fetchall()
        return [r["depends_on_id"] for r in rows]

    # --- Notes ---

    def add_note(self, data: NoteCreate) -> Note:
        id = self._gen_id()
        now = self._now()
        self.conn.execute(
            "INSERT INTO notes (id, entity_type, entity_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (id, data.entity_type, data.entity_id, data.content, now)
        )
        self.conn.commit()
        return Note(id=id, entity_type=data.entity_type, entity_id=data.entity_id,
                   content=data.content, created_at=datetime.fromisoformat(now))

    def get_notes(self, entity_type: str, entity_id: str) -> list[Note]:
        rows = self.conn.execute(
            "SELECT * FROM notes WHERE entity_type = ? AND entity_id = ? ORDER BY created_at",
            (entity_type, entity_id)
        ).fetchall()
        return [Note(id=r["id"], entity_type=r["entity_type"], entity_id=r["entity_id"],
                    content=r["content"], created_at=datetime.fromisoformat(r["created_at"]))
                for r in rows]

    # --- Roadmap View ---

    def get_roadmap(self, org_id: Optional[str] = None) -> RoadmapView:
        """Get full roadmap view with stats."""
        orgs = self.list_orgs()
        if org_id:
            orgs = [o for o in orgs if o.id == org_id]

        org_views = []
        total_features = 0
        features_done = 0
        total_tasks = 0
        tasks_done = 0

        for org in orgs:
            projects = self.list_projects(org.id)
            project_views = []

            for proj in projects:
                features = self.list_features(proj.id)
                feature_views = []
                proj_features_done = 0

                for feat in features:
                    tasks = self.list_tasks(feat.id)
                    task_views = [
                        TaskView(id=t.id, title=t.title, status=t.status,
                                priority=t.priority, complexity=t.complexity)
                        for t in tasks
                    ]
                    feat_tasks_done = sum(1 for t in tasks if t.status in (TaskStatus.DONE, TaskStatus.COMPLETED))

                    feature_views.append(FeatureView(
                        id=feat.id, title=feat.title, status=feat.status,
                        priority=feat.priority, tags=feat.tags, task_count=len(tasks),
                        tasks_done=feat_tasks_done, tasks=task_views
                    ))

                    total_tasks += len(tasks)
                    tasks_done += feat_tasks_done
                    if feat.status in (FeatureStatus.DONE, FeatureStatus.COMPLETED):
                        proj_features_done += 1

                project_views.append(ProjectView(
                    id=proj.id, name=proj.name, description=proj.description,
                    feature_count=len(features), features_done=proj_features_done,
                    features=feature_views
                ))
                total_features += len(features)
                features_done += proj_features_done

            org_views.append(OrgView(id=org.id, name=org.name, projects=project_views))

        return RoadmapView(
            orgs=org_views,
            stats={
                "total_features": total_features,
                "features_done": features_done,
                "total_tasks": total_tasks,
                "tasks_done": tasks_done,
                "completion_pct": round(tasks_done / total_tasks * 100, 1) if total_tasks > 0 else 0
            }
        )
