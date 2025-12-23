"""SQLite database operations for project tracking."""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (
    Complexity,
    Note,
    NoteCreate,
    Org,
    OrgCreate,
    OrgView,
    Priority,
    Project,
    ProjectCreate,
    ProjectView,
    RoadmapView,
    Task,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
    TaskView,
    Ticket,
    TicketCreate,
    TicketStatus,
    TicketUpdate,
    TicketView,
)

# Default database path
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "tpm-mcp" / "tpm.db"


def get_db_path() -> Path:
    """Get database path, creating parent directories if needed."""
    db_path = Path(DEFAULT_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Initialize database with schema."""
    db_path = db_path or get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Read and execute schema
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        conn.executescript(f.read())

    return conn


def _to_json(value: Any) -> str | None:
    """Convert a value to JSON string for storage."""
    if value is None:
        return None
    return json.dumps(value)


def _from_json(value: str | None) -> Any:
    """Parse a JSON string from storage."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _normalize_ticket_status(status: str) -> str:
    """Normalize ticket status (completed -> done)."""
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

    def __init__(self, db_path: Path | None = None):
        self.conn = init_db(db_path)

    def _gen_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def _normalize_id(self, id: str | None) -> str | None:
        """Normalize ID to lowercase for case-insensitive matching."""
        return id.lower() if id else None

    # --- Orgs ---

    def create_org(self, data: OrgCreate) -> Org:
        id = self._gen_id()
        now = self._now()
        self.conn.execute(
            "INSERT INTO orgs (id, name, created_at) VALUES (?, ?, ?)", (id, data.name, now)
        )
        self.conn.commit()
        return Org(id=id, name=data.name, created_at=datetime.fromisoformat(now))

    def create_org_with_id(self, id: str, name: str, created_at: str | None = None) -> Org:
        """Create org with specific ID (for migration)."""
        now = created_at or self._now()
        normalized_id = self._normalize_id(id)
        # Check if a case-insensitive match already exists
        existing = self.conn.execute(
            "SELECT id FROM orgs WHERE LOWER(id) = ?", (normalized_id,)
        ).fetchone()
        if existing:
            id = existing["id"]  # Use existing ID (preserves original case if already exists)
        else:
            id = normalized_id  # Use normalized ID for new entries
        self.conn.execute(
            "INSERT OR REPLACE INTO orgs (id, name, created_at) VALUES (?, ?, ?)", (id, name, now)
        )
        self.conn.commit()
        return Org(id=id, name=name, created_at=datetime.fromisoformat(now))

    def get_org(self, org_id: str) -> Org | None:
        org_id = self._normalize_id(org_id)
        row = self.conn.execute("SELECT * FROM orgs WHERE LOWER(id) = ?", (org_id,)).fetchone()
        if row:
            return Org(
                id=row["id"], name=row["name"], created_at=datetime.fromisoformat(row["created_at"])
            )
        return None

    def list_orgs(self) -> list[Org]:
        rows = self.conn.execute("SELECT * FROM orgs ORDER BY name").fetchall()
        return [
            Org(id=r["id"], name=r["name"], created_at=datetime.fromisoformat(r["created_at"]))
            for r in rows
        ]

    # --- Projects ---

    def create_project(self, data: ProjectCreate) -> Project:
        id = self._gen_id()
        now = self._now()
        normalized_org_id = self._normalize_id(data.org_id)
        # Check if a case-insensitive match already exists for org_id
        existing_org = self.conn.execute(
            "SELECT id FROM orgs WHERE LOWER(id) = ?", (normalized_org_id,)
        ).fetchone()
        if existing_org:
            org_id = existing_org["id"]  # Use existing org ID
        else:
            org_id = normalized_org_id  # Use normalized org_id for new entries
        self.conn.execute(
            """INSERT INTO projects (id, org_id, name, repo_path, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, org_id, data.name, data.repo_path, data.description, now),
        )
        self.conn.commit()
        return Project(
            id=id,
            org_id=org_id,
            name=data.name,
            repo_path=data.repo_path,
            description=data.description,
            created_at=datetime.fromisoformat(now),
        )

    def create_project_with_id(
        self,
        id: str,
        org_id: str,
        name: str,
        repo_path: str | None = None,
        description: str | None = None,
        created_at: str | None = None,
    ) -> Project:
        """Create project with specific ID (for migration)."""
        now = created_at or self._now()
        normalized_id = self._normalize_id(id)
        normalized_org_id = self._normalize_id(org_id)
        # Check if a case-insensitive match already exists for project ID
        existing_project = self.conn.execute(
            "SELECT id FROM projects WHERE LOWER(id) = ?", (normalized_id,)
        ).fetchone()
        if existing_project:
            id = existing_project["id"]  # Use existing ID (preserves original case if already exists)
        else:
            id = normalized_id  # Use normalized ID for new entries
        # Check if a case-insensitive match already exists for org_id
        existing_org = self.conn.execute(
            "SELECT id FROM orgs WHERE LOWER(id) = ?", (normalized_org_id,)
        ).fetchone()
        if existing_org:
            org_id = existing_org["id"]  # Use existing org ID
        else:
            org_id = normalized_org_id  # Use normalized org_id for new entries
        self.conn.execute(
            """INSERT OR REPLACE INTO projects (id, org_id, name, repo_path, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, org_id, name, repo_path, description, now),
        )
        self.conn.commit()
        return Project(
            id=id,
            org_id=org_id,
            name=name,
            repo_path=repo_path,
            description=description,
            created_at=datetime.fromisoformat(now),
        )

    def get_project(self, project_id: str) -> Project | None:
        project_id = self._normalize_id(project_id)
        row = self.conn.execute("SELECT * FROM projects WHERE LOWER(id) = ?", (project_id,)).fetchone()
        if row:
            return Project(
                id=row["id"],
                org_id=row["org_id"],
                name=row["name"],
                repo_path=row["repo_path"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        return None

    def list_projects(self, org_id: str | None = None) -> list[Project]:
        if org_id:
            org_id = self._normalize_id(org_id)
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE LOWER(org_id) = ? ORDER BY name", (org_id,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
        return [
            Project(
                id=r["id"],
                org_id=r["org_id"],
                name=r["name"],
                repo_path=r["repo_path"],
                description=r["description"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    # --- Tickets ---

    def _get_next_ticket_number(self, prefix: str) -> int:
        """Get the next sequential number for tickets with given prefix."""
        # Find max existing number for this prefix (e.g., SENTRY-003 -> 3)
        rows = self.conn.execute(
            "SELECT id FROM tickets WHERE id LIKE ?", (f"{prefix}-%",)
        ).fetchall()
        max_num = 0
        for row in rows:
            try:
                # Extract number after prefix (e.g., "SENTRY-003" -> 3)
                num_str = row["id"].split("-")[-1]
                num = int(num_str)
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                continue
        return max_num + 1

    def create_ticket(self, data: TicketCreate) -> Ticket:
        normalized_project_id = self._normalize_id(data.project_id)
        # Check if a case-insensitive match already exists for project_id
        existing_project = self.conn.execute(
            "SELECT id FROM projects WHERE LOWER(id) = ?", (normalized_project_id,)
        ).fetchone()
        if existing_project:
            project_id = existing_project["id"]  # Use existing project ID
        else:
            project_id = normalized_project_id  # Use normalized project_id for new entries
        # Determine prefix for ID generation
        if data.prefix:
            # Use provided prefix (e.g., FEAT, ISSUE, INFRA)
            prefix = data.prefix.upper().replace(" ", "").replace("-", "").replace("_", "")
        else:
            # Auto-generate prefix from project ID
            project = self.get_project(project_id)
            if project:
                prefix = project.id.upper().replace(" ", "").replace("-", "").replace("_", "")
            else:
                prefix = "TICKET"
        next_num = self._get_next_ticket_number(prefix)
        id = f"{prefix}-{next_num:03d}"
        now = self._now()
        self.conn.execute(
            """INSERT INTO tickets (id, project_id, title, description, status, priority, created_at,
               assignees, tags, related_repos, acceptance_criteria, blockers, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                id,
                project_id,
                data.title,
                data.description,
                data.status.value,
                data.priority.value,
                now,
                _to_json(data.assignees),
                _to_json(data.tags),
                _to_json(data.related_repos),
                _to_json(data.acceptance_criteria),
                _to_json(data.blockers),
                _to_json(data.metadata),
            ),
        )
        self.conn.commit()
        return Ticket(
            id=id,
            project_id=project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            created_at=datetime.fromisoformat(now),
            assignees=data.assignees,
            tags=data.tags,
            related_repos=data.related_repos,
            acceptance_criteria=data.acceptance_criteria,
            blockers=data.blockers,
            metadata=data.metadata,
        )

    def create_ticket_with_id(
        self,
        id: str,
        project_id: str,
        title: str,
        description: str | None = None,
        status: str = "backlog",
        priority: str = "medium",
        created_at: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        assignees: list | None = None,
        tags: list | None = None,
        related_repos: list | None = None,
        acceptance_criteria: list | None = None,
        blockers: list | None = None,
        metadata: dict | None = None,
    ) -> Ticket:
        """Create ticket with specific ID (for migration)."""
        now = created_at or self._now()
        status = _normalize_ticket_status(status)
        normalized_project_id = self._normalize_id(project_id)
        # Check if a case-insensitive match already exists for project_id
        existing_project = self.conn.execute(
            "SELECT id FROM projects WHERE LOWER(id) = ?", (normalized_project_id,)
        ).fetchone()
        if existing_project:
            project_id = existing_project["id"]  # Use existing project ID
        else:
            project_id = normalized_project_id  # Use normalized project_id for new entries
        self.conn.execute(
            """INSERT OR REPLACE INTO tickets (id, project_id, title, description, status, priority,
               created_at, started_at, completed_at, assignees, tags, related_repos,
               acceptance_criteria, blockers, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                id,
                project_id,
                title,
                description,
                status,
                priority,
                now,
                started_at,
                completed_at,
                _to_json(assignees),
                _to_json(tags),
                _to_json(related_repos),
                _to_json(acceptance_criteria),
                _to_json(blockers),
                _to_json(metadata),
            ),
        )
        self.conn.commit()
        return self.get_ticket(id)

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        row = self.conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row:
            return self._row_to_ticket(row)
        return None

    def _row_to_ticket(self, row) -> Ticket:
        status = _normalize_ticket_status(row["status"])
        return Ticket(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            description=row["description"],
            status=TicketStatus(status),
            priority=Priority(row["priority"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
            assignees=_from_json(row["assignees"]),
            tags=_from_json(row["tags"]),
            related_repos=_from_json(row["related_repos"]),
            acceptance_criteria=_from_json(row["acceptance_criteria"]),
            blockers=_from_json(row["blockers"]),
            metadata=_from_json(row["metadata"]),
        )

    def list_tickets(
        self, project_id: str | None = None, status: TicketStatus | None = None
    ) -> list[Ticket]:
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []
        if project_id:
            project_id = self._normalize_id(project_id)
            query += " AND LOWER(project_id) = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY priority, created_at"
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_ticket(r) for r in rows]

    def search_tickets(
        self,
        query: str,
        project_id: str | None = None,
        status: TicketStatus | None = None,
        priority: Priority | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Search tickets using full-text search with optional filters.

        Args:
            query: Search query (supports prefix matching)
            project_id: Filter by project ID (case-insensitive)
            status: Filter by ticket status
            priority: Filter by priority level
            tags: Filter by tags (ticket must have all specified tags)
            limit: Maximum results to return (default 20)

        Returns:
            List of dicts with: id, title, project_id, status, priority, tags, snippet
        """
        if not query or not query.strip():
            return []

        # Build FTS5 query with prefix matching for each term
        terms = query.strip().split()
        fts_query = " ".join(f"{term}*" for term in terms)

        # Build the SQL query with joins and filters
        sql = """
            SELECT
                t.id,
                t.title,
                t.project_id,
                t.status,
                t.priority,
                t.tags,
                snippet(tickets_fts, 1, '<b>', '</b>', '...', 32) as snippet
            FROM tickets_fts
            JOIN tickets t ON tickets_fts.ticket_id = t.id
            WHERE tickets_fts MATCH ?
        """
        params: list = [fts_query]

        # Add filters
        if project_id:
            project_id = self._normalize_id(project_id)
            sql += " AND LOWER(t.project_id) = ?"
            params.append(project_id)

        if status:
            sql += " AND t.status = ?"
            params.append(status.value)

        if priority:
            sql += " AND t.priority = ?"
            params.append(priority.value)

        if tags:
            # Check that ticket has all specified tags using json_each
            for tag in tags:
                sql += " AND EXISTS (SELECT 1 FROM json_each(t.tags) WHERE value = ?)"
                params.append(tag)

        # Order by relevance (FTS5 rank) and limit
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        try:
            rows = self.conn.execute(sql, params).fetchall()
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "project_id": r["project_id"],
                    "status": r["status"],
                    "priority": r["priority"],
                    "tags": _from_json(r["tags"]),
                    "snippet": r["snippet"],
                }
                for r in rows
            ]
        except Exception:
            # Handle FTS5 syntax errors gracefully
            return []

    def update_ticket(self, ticket_id: str, data: TicketUpdate) -> Ticket | None:
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
            if data.status == TicketStatus.IN_PROGRESS:
                updates.append("started_at = ?")
                params.append(self._now())
            elif data.status in (TicketStatus.DONE, TicketStatus.COMPLETED):
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
            return self.get_ticket(ticket_id)

        params.append(ticket_id)
        self.conn.execute(f"UPDATE tickets SET {', '.join(updates)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_ticket(ticket_id)

    # --- Tasks ---

    def create_task(self, data: TaskCreate) -> Task:
        # Get ticket to extract prefix
        ticket = self.get_ticket(data.ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {data.ticket_id} not found")

        # Count existing tasks for this ticket to generate task number
        count = self.conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE ticket_id = ?", (data.ticket_id,)
        ).fetchone()[0]

        # Generate task ID like TASK-TICKET-001-1
        ticket_num = ticket.id.replace("TICKET-", "").replace("FEAT-", "").replace("ISSUE-", "")
        id = f"TASK-{ticket_num}-{count + 1}"
        now = self._now()

        self.conn.execute(
            """INSERT INTO tasks (id, ticket_id, title, details, status, priority, complexity,
               created_at, acceptance_criteria, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                id,
                data.ticket_id,
                data.title,
                data.details,
                data.status.value,
                data.priority.value,
                data.complexity.value,
                now,
                _to_json(data.acceptance_criteria),
                _to_json(data.metadata),
            ),
        )
        self.conn.commit()
        return Task(
            id=id,
            ticket_id=data.ticket_id,
            title=data.title,
            details=data.details,
            status=data.status,
            priority=data.priority,
            complexity=data.complexity,
            created_at=datetime.fromisoformat(now),
            acceptance_criteria=data.acceptance_criteria,
            metadata=data.metadata,
        )

    def create_task_with_id(
        self,
        id: str,
        ticket_id: str,
        title: str,
        details: str | None = None,
        status: str = "pending",
        priority: str = "medium",
        complexity: str = "medium",
        created_at: str | None = None,
        completed_at: str | None = None,
        acceptance_criteria: list | None = None,
        metadata: dict | None = None,
    ) -> Task:
        """Create task with specific ID (for migration)."""
        now = created_at or self._now()
        status = _normalize_task_status(status)
        self.conn.execute(
            """INSERT OR REPLACE INTO tasks (id, ticket_id, title, details, status, priority, complexity,
               created_at, completed_at, acceptance_criteria, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                id,
                ticket_id,
                title,
                details,
                status,
                priority,
                complexity,
                now,
                completed_at,
                _to_json(acceptance_criteria),
                _to_json(metadata),
            ),
        )
        self.conn.commit()
        return self.get_task(id)

    def get_task(self, task_id: str) -> Task | None:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            return self._row_to_task(row)
        return None

    def _row_to_task(self, row) -> Task:
        status = _normalize_task_status(row["status"])
        return Task(
            id=row["id"],
            ticket_id=row["ticket_id"],
            title=row["title"],
            details=row["details"],
            status=TaskStatus(status),
            priority=Priority(row["priority"] or "medium"),
            complexity=Complexity(row["complexity"] or "medium"),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"])
            if row["completed_at"]
            else None,
            acceptance_criteria=_from_json(row["acceptance_criteria"]),
            metadata=_from_json(row["metadata"]),
        )

    def list_tasks(
        self, ticket_id: str | None = None, status: TaskStatus | None = None
    ) -> list[Task]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if ticket_id:
            query += " AND ticket_id = ?"
            params.append(ticket_id)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at"
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def update_task(self, task_id: str, data: TaskUpdate) -> Task | None:
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
        self.conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_task(task_id)

    # --- Task Dependencies ---

    def add_task_dependency(self, task_id: str, depends_on_id: str) -> bool:
        """Add a dependency between tasks."""
        try:
            self.conn.execute(
                "INSERT INTO task_dependencies (task_id, depends_on_id) VALUES (?, ?)",
                (task_id, depends_on_id),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_task_dependencies(self, task_id: str) -> list[str]:
        """Get IDs of tasks that this task depends on."""
        rows = self.conn.execute(
            "SELECT depends_on_id FROM task_dependencies WHERE task_id = ?", (task_id,)
        ).fetchall()
        return [r["depends_on_id"] for r in rows]

    # --- Notes ---

    def add_note(self, data: NoteCreate) -> Note:
        id = self._gen_id()
        now = self._now()
        self.conn.execute(
            "INSERT INTO notes (id, entity_type, entity_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (id, data.entity_type, data.entity_id, data.content, now),
        )
        self.conn.commit()
        return Note(
            id=id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            content=data.content,
            created_at=datetime.fromisoformat(now),
        )

    def get_notes(self, entity_type: str, entity_id: str) -> list[Note]:
        rows = self.conn.execute(
            "SELECT * FROM notes WHERE entity_type = ? AND entity_id = ? ORDER BY created_at",
            (entity_type, entity_id),
        ).fetchall()
        return [
            Note(
                id=r["id"],
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                content=r["content"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    def get_note(self, note_id: str) -> Note | None:
        row = self.conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row:
            return Note(
                id=row["id"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        return None

    # --- Roadmap View ---

    def get_roadmap(self, org_id: str | None = None) -> RoadmapView:
        """Get full roadmap view with stats."""
        orgs = self.list_orgs()
        if org_id:
            org_id = self._normalize_id(org_id)
            orgs = [o for o in orgs if o.id.lower() == org_id]

        org_views = []
        total_tickets = 0
        tickets_done = 0
        total_tasks = 0
        tasks_done = 0

        for org in orgs:
            projects = self.list_projects(org.id)
            project_views = []

            for proj in projects:
                tickets = self.list_tickets(proj.id)
                ticket_views = []
                proj_tickets_done = 0

                for ticket in tickets:
                    tasks = self.list_tasks(ticket.id)
                    task_views = [
                        TaskView(
                            id=t.id,
                            title=t.title,
                            status=t.status,
                            priority=t.priority,
                            complexity=t.complexity,
                        )
                        for t in tasks
                    ]
                    ticket_tasks_done = sum(
                        1 for t in tasks if t.status in (TaskStatus.DONE, TaskStatus.COMPLETED)
                    )

                    ticket_views.append(
                        TicketView(
                            id=ticket.id,
                            title=ticket.title,
                            status=ticket.status,
                            priority=ticket.priority,
                            tags=ticket.tags,
                            task_count=len(tasks),
                            tasks_done=ticket_tasks_done,
                            tasks=task_views,
                        )
                    )

                    total_tasks += len(tasks)
                    tasks_done += ticket_tasks_done
                    if ticket.status in (TicketStatus.DONE, TicketStatus.COMPLETED):
                        proj_tickets_done += 1

                project_views.append(
                    ProjectView(
                        id=proj.id,
                        name=proj.name,
                        description=proj.description,
                        ticket_count=len(tickets),
                        tickets_done=proj_tickets_done,
                        tickets=ticket_views,
                    )
                )
                total_tickets += len(tickets)
                tickets_done += proj_tickets_done

            org_views.append(OrgView(id=org.id, name=org.name, projects=project_views))

        return RoadmapView(
            orgs=org_views,
            stats={
                "total_tickets": total_tickets,
                "tickets_done": tickets_done,
                "total_tasks": total_tasks,
                "tasks_done": tasks_done,
                "completion_pct": round(tasks_done / total_tasks * 100, 1)
                if total_tasks > 0
                else 0,
            },
        )
