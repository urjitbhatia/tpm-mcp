"""Tests for database operations."""
import tempfile
from pathlib import Path

import pytest

from tpm_mcp.db import TrackerDB
from tpm_mcp.models import (
    OrgCreate, ProjectCreate, TicketCreate, TicketUpdate,
    TaskCreate, TaskUpdate, NoteCreate,
    TicketStatus, TaskStatus, Priority, Complexity
)


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db = TrackerDB(db_path)
    yield db

    # Cleanup
    db.conn.close()
    db_path.unlink(missing_ok=True)
    # Also remove WAL files
    Path(str(db_path) + "-wal").unlink(missing_ok=True)
    Path(str(db_path) + "-shm").unlink(missing_ok=True)


class TestOrgs:
    def test_create_org(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        assert org.id is not None
        assert org.name == "Test Org"
        assert org.created_at is not None

    def test_create_org_with_id(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        assert org.id == "test-org"
        assert org.name == "Test Org"

    def test_get_org(self, db):
        created = db.create_org(OrgCreate(name="Test Org"))
        fetched = db.get_org(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    def test_get_org_not_found(self, db):
        fetched = db.get_org("nonexistent")
        assert fetched is None

    def test_list_orgs(self, db):
        db.create_org(OrgCreate(name="Alpha"))
        db.create_org(OrgCreate(name="Beta"))
        orgs = db.list_orgs()
        assert len(orgs) == 2
        assert orgs[0].name == "Alpha"  # Sorted by name
        assert orgs[1].name == "Beta"

    def test_get_org_case_insensitive(self, db):
        """Test that org lookups are case-insensitive."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        # Try fetching with different cases
        assert db.get_org("TEST-ORG") is not None
        assert db.get_org("Test-Org") is not None
        assert db.get_org("test-org") is not None
        fetched = db.get_org("TEST-ORG")
        assert fetched.id == org.id
        assert fetched.name == org.name

    def test_create_org_with_id_case_insensitive_reuse(self, db):
        """Test that creating org with different case reuses existing ID."""
        org1 = db.create_org_with_id(id="test-org", name="Test Org")
        # Create with different case - should reuse existing
        org2 = db.create_org_with_id(id="TEST-ORG", name="Test Org Updated")
        assert org1.id == org2.id  # Should reuse same ID
        assert org2.name == "Test Org Updated"  # But update name


class TestProjects:
    def test_create_project(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(
            org_id=org.id,
            name="Test Project",
            description="A test project",
            repo_path="/path/to/repo"
        ))
        assert project.id is not None
        assert project.org_id == org.id
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.repo_path == "/path/to/repo"

    def test_create_project_with_id(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(
            id="test-project",
            org_id=org.id,
            name="Test Project"
        )
        assert project.id == "test-project"

    def test_list_projects_by_org(self, db):
        org1 = db.create_org(OrgCreate(name="Org 1"))
        org2 = db.create_org(OrgCreate(name="Org 2"))
        db.create_project(ProjectCreate(org_id=org1.id, name="Project A"))
        db.create_project(ProjectCreate(org_id=org1.id, name="Project B"))
        db.create_project(ProjectCreate(org_id=org2.id, name="Project C"))

        projects = db.list_projects(org1.id)
        assert len(projects) == 2
        assert all(p.org_id == org1.id for p in projects)

    def test_get_project_case_insensitive(self, db):
        """Test that project lookups are case-insensitive."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        # Try fetching with different cases
        assert db.get_project("TEST-PROJECT") is not None
        assert db.get_project("Test-Project") is not None
        assert db.get_project("test-project") is not None
        fetched = db.get_project("TEST-PROJECT")
        assert fetched.id == project.id
        assert fetched.name == project.name

    def test_list_projects_case_insensitive(self, db):
        """Test that filtering projects by org_id is case-insensitive."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        db.create_project(ProjectCreate(org_id=org.id, name="Project A"))
        db.create_project(ProjectCreate(org_id=org.id, name="Project B"))
        # Try listing with different cases
        projects1 = db.list_projects("TEST-ORG")
        projects2 = db.list_projects("Test-Org")
        projects3 = db.list_projects("test-org")
        assert len(projects1) == 2
        assert len(projects2) == 2
        assert len(projects3) == 2
        assert projects1[0].id == projects2[0].id == projects3[0].id

    def test_create_project_with_id_case_insensitive_reuse(self, db):
        """Test that creating project with different case reuses existing IDs."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project1 = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        # Create with different case - should reuse existing
        project2 = db.create_project_with_id(id="TEST-PROJECT", org_id="TEST-ORG", name="Test Project Updated")
        assert project1.id == project2.id  # Should reuse same project ID
        assert project2.org_id == org.id  # Should reuse same org ID
        assert project2.name == "Test Project Updated"  # But update name


class TestTickets:
    def test_create_ticket_auto_id(self, db):
        """Test that auto-generated ticket ID uses project ID as prefix with sequential number."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        ticket1 = db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Test Ticket 1",
            description="A test ticket",
            status=TicketStatus.PLANNED,
            priority=Priority.HIGH,
            tags=["test", "ticket"],
            assignees=["Staff Engineer"]
        ))

        ticket2 = db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Test Ticket 2",
        ))

        # Auto-generated ID should use project ID (uppercased) as prefix with sequential numbers
        prefix = project.id.upper().replace("-", "").replace("_", "")
        assert ticket1.id == f"{prefix}-001"
        assert ticket2.id == f"{prefix}-002"
        assert ticket1.title == "Test Ticket 1"
        assert ticket1.status == TicketStatus.PLANNED
        assert ticket1.priority == Priority.HIGH
        assert ticket1.tags == ["test", "ticket"]
        assert ticket1.assignees == ["Staff Engineer"]

    def test_create_ticket_custom_id(self, db):
        """Test that custom ticket ID is used when provided."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        ticket = db.create_ticket(TicketCreate(
            project_id=project.id,
            id="FEAT-001",
            title="Custom ID Ticket",
        ))

        assert ticket.id == "FEAT-001"
        assert ticket.title == "Custom ID Ticket"

    def test_create_ticket_with_id(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")

        ticket = db.create_ticket_with_id(
            id="FEAT-001",
            project_id=project.id,
            title="Test Ticket",
            status="in-progress",
            priority="high",
            tags=["api", "backend"],
            metadata={"architecture": {"decision": "Use FastAPI"}}
        )

        assert ticket.id == "FEAT-001"
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.tags == ["api", "backend"]
        assert ticket.metadata == {"architecture": {"decision": "Use FastAPI"}}

    def test_ticket_status_normalization(self, db):
        """Test that 'completed' status is normalized to 'done'."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")

        ticket = db.create_ticket_with_id(
            id="FEAT-001",
            project_id=project.id,
            title="Test Ticket",
            status="completed"  # Should be normalized to "done"
        )

        assert ticket.status == TicketStatus.DONE

    def test_update_ticket(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        ticket = db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Test Ticket"
        ))

        updated = db.update_ticket(ticket.id, TicketUpdate(
            title="Updated Ticket",
            status=TicketStatus.IN_PROGRESS,
            tags=["updated"]
        ))

        assert updated.title == "Updated Ticket"
        assert updated.status == TicketStatus.IN_PROGRESS
        assert updated.started_at is not None  # Should be set when status changes to in-progress
        assert updated.tags == ["updated"]

    def test_list_tickets_by_status(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(project_id=project.id, title="Ticket 1", status=TicketStatus.BACKLOG))
        db.create_ticket(TicketCreate(project_id=project.id, title="Ticket 2", status=TicketStatus.IN_PROGRESS))
        db.create_ticket(TicketCreate(project_id=project.id, title="Ticket 3", status=TicketStatus.DONE))

        in_progress = db.list_tickets(status=TicketStatus.IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].title == "Ticket 2"

    def test_list_tickets_case_insensitive(self, db):
        """Test that filtering tickets by project_id is case-insensitive."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        db.create_ticket(TicketCreate(project_id=project.id, title="Ticket 1"))
        db.create_ticket(TicketCreate(project_id=project.id, title="Ticket 2"))
        # Try listing with different cases
        tickets1 = db.list_tickets(project_id="TEST-PROJECT")
        tickets2 = db.list_tickets(project_id="Test-Project")
        tickets3 = db.list_tickets(project_id="test-project")
        assert len(tickets1) == 2
        assert len(tickets2) == 2
        assert len(tickets3) == 2
        assert tickets1[0].id == tickets2[0].id == tickets3[0].id

    def test_create_ticket_case_insensitive_project_id(self, db):
        """Test that creating tickets with different case project_id works."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        # Create ticket with different case project_id
        ticket = db.create_ticket(TicketCreate(project_id="TEST-PROJECT", title="Test Ticket"))
        assert ticket.project_id == project.id  # Should use existing project ID
        assert ticket.title == "Test Ticket"


class TestTasks:
    def test_create_task(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        ticket = db.create_ticket(TicketCreate(project_id=project.id, title="Test Ticket"))

        task = db.create_task(TaskCreate(
            ticket_id=ticket.id,
            title="Test Task",
            details="Task details",
            status=TaskStatus.PENDING,
            priority=Priority.HIGH,
            complexity=Complexity.MEDIUM,
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        ))

        assert task.id.startswith("TASK-")
        assert task.title == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.HIGH
        assert task.acceptance_criteria == ["Criteria 1", "Criteria 2"]

    def test_create_task_with_id(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        ticket = db.create_ticket_with_id(id="FEAT-001", project_id=project.id, title="Test Ticket")

        task = db.create_task_with_id(
            id="TASK-001-1",
            ticket_id=ticket.id,
            title="Test Task",
            status="completed",  # Should be normalized to "done"
            metadata={"filesCreated": ["/path/to/file.py"]}
        )

        assert task.id == "TASK-001-1"
        assert task.status == TaskStatus.DONE
        assert task.metadata == {"filesCreated": ["/path/to/file.py"]}

    def test_task_auto_numbering(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        ticket = db.create_ticket(TicketCreate(project_id=project.id, title="Test Ticket"))

        task1 = db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 1"))
        task2 = db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 2"))
        task3 = db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 3"))

        # IDs should be sequential
        assert "-1" in task1.id
        assert "-2" in task2.id
        assert "-3" in task3.id

    def test_update_task_sets_completed_at(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        ticket = db.create_ticket(TicketCreate(project_id=project.id, title="Test Ticket"))
        task = db.create_task(TaskCreate(ticket_id=ticket.id, title="Test Task"))

        assert task.completed_at is None

        updated = db.update_task(task.id, TaskUpdate(status=TaskStatus.DONE))
        assert updated.completed_at is not None

    def test_task_dependencies(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        ticket = db.create_ticket(TicketCreate(project_id=project.id, title="Test Ticket"))

        task1 = db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 1"))
        task2 = db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 2"))

        db.add_task_dependency(task2.id, task1.id)
        deps = db.get_task_dependencies(task2.id)

        assert len(deps) == 1
        assert deps[0] == task1.id


class TestNotes:
    def test_add_note(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))

        note = db.add_note(NoteCreate(
            entity_type="org",
            entity_id=org.id,
            content="This is a note"
        ))

        assert note.id is not None
        assert note.content == "This is a note"

    def test_get_notes(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))

        db.add_note(NoteCreate(entity_type="org", entity_id=org.id, content="Note 1"))
        db.add_note(NoteCreate(entity_type="org", entity_id=org.id, content="Note 2"))

        notes = db.get_notes("org", org.id)
        assert len(notes) == 2


class TestRoadmapView:
    def test_get_roadmap(self, db):
        # Create test data
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        ticket = db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Test Ticket",
            status=TicketStatus.IN_PROGRESS,
            tags=["api"]
        ))
        db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 1", status=TaskStatus.DONE))
        db.create_task(TaskCreate(ticket_id=ticket.id, title="Task 2", status=TaskStatus.PENDING))

        roadmap = db.get_roadmap()

        assert len(roadmap.orgs) == 1
        assert roadmap.orgs[0].name == "Test Org"
        assert len(roadmap.orgs[0].projects) == 1
        assert len(roadmap.orgs[0].projects[0].tickets) == 1
        assert roadmap.orgs[0].projects[0].tickets[0].tags == ["api"]
        assert roadmap.orgs[0].projects[0].tickets[0].tasks_done == 1
        assert roadmap.orgs[0].projects[0].tickets[0].task_count == 2

        assert roadmap.stats["total_tickets"] == 1
        assert roadmap.stats["total_tasks"] == 2
        assert roadmap.stats["tasks_done"] == 1
        assert roadmap.stats["completion_pct"] == 50.0

    def test_get_roadmap_by_org(self, db):
        org1 = db.create_org(OrgCreate(name="Org 1"))
        org2 = db.create_org(OrgCreate(name="Org 2"))
        db.create_project(ProjectCreate(org_id=org1.id, name="Project 1"))
        db.create_project(ProjectCreate(org_id=org2.id, name="Project 2"))

        roadmap = db.get_roadmap(org1.id)

        assert len(roadmap.orgs) == 1
        assert roadmap.orgs[0].id == org1.id

    def test_get_roadmap_case_insensitive(self, db):
        """Test that roadmap filtering by org_id is case-insensitive."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        db.create_project(ProjectCreate(org_id=org.id, name="Project 1"))
        # Try getting roadmap with different cases
        roadmap1 = db.get_roadmap("TEST-ORG")
        roadmap2 = db.get_roadmap("Test-Org")
        roadmap3 = db.get_roadmap("test-org")
        assert len(roadmap1.orgs) == 1
        assert len(roadmap2.orgs) == 1
        assert len(roadmap3.orgs) == 1
        assert roadmap1.orgs[0].id == roadmap2.orgs[0].id == roadmap3.orgs[0].id


class TestJsonSerialization:
    def test_ticket_with_complex_metadata(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")

        complex_metadata = {
            "architecture": {
                "decision": "Use FastAPI",
                "reasoning": ["Performance", "Async support"],
                "files": ["/src/main.py", "/src/routes.py"]
            },
            "implementationPlan": {
                "phase1": {"status": "done", "tasks": 5},
                "phase2": {"status": "pending", "tasks": 3}
            }
        }

        _ = db.create_ticket_with_id(
            id="FEAT-001",
            project_id=project.id,
            title="Test Ticket",
            metadata=complex_metadata
        )

        # Fetch and verify
        fetched = db.get_ticket("FEAT-001")
        assert fetched.metadata == complex_metadata
        assert fetched.metadata["architecture"]["reasoning"] == ["Performance", "Async support"]

    def test_task_with_files_metadata(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        ticket = db.create_ticket_with_id(id="FEAT-001", project_id=project.id, title="Test Ticket")

        task_metadata = {
            "filesCreated": ["/src/new_file.py"],
            "filesModified": ["/src/existing.py"],
            "testResults": {"passed": 10, "failed": 0, "coverage": 95.5}
        }

        _ = db.create_task_with_id(
            id="TASK-001-1",
            ticket_id=ticket.id,
            title="Test Task",
            metadata=task_metadata
        )

        fetched = db.get_task("TASK-001-1")
        assert fetched.metadata == task_metadata
        assert fetched.metadata["testResults"]["coverage"] == 95.5
