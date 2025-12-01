"""SQLite database operations for project tracking."""
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    Org, OrgCreate,
    Project, ProjectCreate,
    Feature, FeatureCreate, FeatureUpdate, FeatureStatus,
    Task, TaskCreate, TaskUpdate, TaskStatus,
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
            """INSERT INTO features (id, project_id, title, description, status, priority, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, data.project_id, data.title, data.description,
             data.status.value, data.priority.value, now)
        )
        self.conn.commit()
        return Feature(id=id, project_id=data.project_id, title=data.title,
                      description=data.description, status=data.status,
                      priority=data.priority, created_at=datetime.fromisoformat(now))

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        row = self.conn.execute(
            "SELECT * FROM features WHERE id = ?", (feature_id,)
        ).fetchone()
        if row:
            return self._row_to_feature(row)
        return None

    def _row_to_feature(self, row) -> Feature:
        return Feature(
            id=row["id"], project_id=row["project_id"], title=row["title"],
            description=row["description"], status=FeatureStatus(row["status"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
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
            elif data.status == FeatureStatus.DONE:
                updates.append("completed_at = ?")
                params.append(self._now())
        if data.priority is not None:
            updates.append("priority = ?")
            params.append(data.priority.value)

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
            """INSERT INTO tasks (id, feature_id, title, details, status, complexity, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (id, data.feature_id, data.title, data.details,
             data.status.value, data.complexity.value, now)
        )
        self.conn.commit()
        return Task(id=id, feature_id=data.feature_id, title=data.title,
                   details=data.details, status=data.status,
                   complexity=data.complexity, created_at=datetime.fromisoformat(now))

    def get_task(self, task_id: str) -> Optional[Task]:
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row:
            return self._row_to_task(row)
        return None

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row["id"], feature_id=row["feature_id"], title=row["title"],
            details=row["details"], status=TaskStatus(row["status"]),
            complexity=row["complexity"],
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
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
            if data.status == TaskStatus.DONE:
                updates.append("completed_at = ?")
                params.append(self._now())
        if data.complexity is not None:
            updates.append("complexity = ?")
            params.append(data.complexity.value)

        if not updates:
            return self.get_task(task_id)

        params.append(task_id)
        self.conn.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params
        )
        self.conn.commit()
        return self.get_task(task_id)

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
                        TaskView(id=t.id, title=t.title, status=t.status, complexity=t.complexity)
                        for t in tasks
                    ]
                    feat_tasks_done = sum(1 for t in tasks if t.status == TaskStatus.DONE)

                    feature_views.append(FeatureView(
                        id=feat.id, title=feat.title, status=feat.status,
                        priority=feat.priority, task_count=len(tasks),
                        tasks_done=feat_tasks_done, tasks=task_views
                    ))

                    total_tasks += len(tasks)
                    tasks_done += feat_tasks_done
                    if feat.status == FeatureStatus.DONE:
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
