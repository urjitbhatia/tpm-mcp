"""Tests for MCP server tool handlers."""
import json
import tempfile
from pathlib import Path

import pytest

from tpm_mcp.db import TrackerDB
from tpm_mcp.models import (
    NoteCreate,
    OrgCreate,
    ProjectCreate,
    TaskCreate,
    TaskStatus,
    TicketCreate,
    TicketStatus,
)
from tpm_mcp.server import _handle_tool


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    test_db = TrackerDB(db_path)

    # Replace the server's db with our test db
    import tpm_mcp.server as server_module
    original_db = server_module.db
    server_module.db = test_db

    yield test_db

    # Restore original db and cleanup
    server_module.db = original_db
    test_db.conn.close()
    db_path.unlink(missing_ok=True)
    Path(str(db_path) + "-wal").unlink(missing_ok=True)
    Path(str(db_path) + "-shm").unlink(missing_ok=True)


@pytest.fixture
def sample_data(db):
    """Create sample org, project, tickets, tasks for testing."""
    org = db.create_org(OrgCreate(name="Test Org"))
    project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

    tickets = []
    for i in range(5):
        ticket = db.create_ticket(TicketCreate(
            project_id=project.id,
            title=f"Ticket {i+1}",
            status=TicketStatus.IN_PROGRESS if i < 2 else TicketStatus.DONE,
        ))
        tickets.append(ticket)

        # Add tasks to each ticket
        for j in range(3):
            db.create_task(TaskCreate(
                ticket_id=ticket.id,
                title=f"Task {j+1} for Ticket {i+1}",
                status=TaskStatus.DONE if j == 0 else TaskStatus.PENDING,
            ))

    # Add notes
    for i, ticket in enumerate(tickets[:2]):
        db.add_note(NoteCreate(
            entity_type="ticket",
            entity_id=ticket.id,
            content=f"This is a note for ticket {i+1}. " * 20  # Long content
        ))

    return {"org": org, "project": project, "tickets": tickets}


class TestTicketList:
    @pytest.mark.asyncio
    async def test_returns_minimal_data(self, db, sample_data):
        """Test that ticket_list returns only id, status, priority."""
        result = await _handle_tool("ticket_list", {"project_id": sample_data["project"].id})
        data = json.loads(result)

        assert "tickets" in data
        assert "total" in data
        assert data["total"] == 5

        # Check first ticket has only minimal fields
        ticket = data["tickets"][0]
        assert "id" in ticket
        assert "status" in ticket
        assert "priority" in ticket
        # Should NOT have title, description, tags, etc.
        assert "title" not in ticket
        assert "description" not in ticket
        assert "tags" not in ticket

    @pytest.mark.asyncio
    async def test_pagination(self, db, sample_data):
        """Test pagination with limit and offset."""
        # Get first 2
        result = await _handle_tool("ticket_list", {
            "project_id": sample_data["project"].id,
            "limit": 2,
            "offset": 0
        })
        data = json.loads(result)
        assert len(data["tickets"]) == 2
        assert data["offset"] == 0
        assert data["limit"] == 2
        assert data["total"] == 5

        # Get next 2
        result = await _handle_tool("ticket_list", {
            "project_id": sample_data["project"].id,
            "limit": 2,
            "offset": 2
        })
        data = json.loads(result)
        assert len(data["tickets"]) == 2
        assert data["offset"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db, sample_data):
        """Test filtering by status."""
        result = await _handle_tool("ticket_list", {
            "project_id": sample_data["project"].id,
            "status": "done"
        })
        data = json.loads(result)
        assert data["total"] == 3  # 3 done tickets
        for ticket in data["tickets"]:
            assert ticket["status"] == "done"


class TestTaskList:
    @pytest.mark.asyncio
    async def test_returns_minimal_data(self, db, sample_data):
        """Test that task_list returns only id, ticket_id, status."""
        ticket = sample_data["tickets"][0]
        result = await _handle_tool("task_list", {"ticket_id": ticket.id})
        data = json.loads(result)

        assert "tasks" in data
        assert "total" in data
        assert data["total"] == 3

        # Check first task has only minimal fields
        task = data["tasks"][0]
        assert "id" in task
        assert "ticket_id" in task
        assert "status" in task
        # Should NOT have title, details, priority, complexity
        assert "title" not in task
        assert "details" not in task
        assert "priority" not in task

    @pytest.mark.asyncio
    async def test_pagination(self, db, sample_data):
        """Test pagination with limit and offset."""
        ticket = sample_data["tickets"][0]
        result = await _handle_tool("task_list", {
            "ticket_id": ticket.id,
            "limit": 2,
            "offset": 0
        })
        data = json.loads(result)
        assert len(data["tasks"]) == 2
        assert data["offset"] == 0
        assert data["total"] == 3


class TestNoteList:
    @pytest.mark.asyncio
    async def test_returns_preview(self, db, sample_data):
        """Test that note_list returns id, created_at, and preview."""
        ticket = sample_data["tickets"][0]
        result = await _handle_tool("note_list", {
            "entity_type": "ticket",
            "entity_id": ticket.id
        })
        data = json.loads(result)

        assert "notes" in data
        assert "total" in data
        assert data["total"] == 1

        note = data["notes"][0]
        assert "id" in note
        assert "created_at" in note
        assert "preview" in note
        # Preview should be truncated
        assert len(note["preview"]) <= 103  # 100 chars + "..."
        # Should NOT have full content
        assert "content" not in note


class TestNoteGet:
    @pytest.mark.asyncio
    async def test_returns_full_content(self, db, sample_data):
        """Test that note_get returns full note content."""
        ticket = sample_data["tickets"][0]
        notes = db.get_notes("ticket", ticket.id)
        note = notes[0]

        result = await _handle_tool("note_get", {"note_id": note.id})
        data = json.loads(result)

        assert "id" in data
        assert "content" in data
        assert data["content"] == note.content  # Full content
        assert len(data["content"]) > 100  # Longer than preview

    @pytest.mark.asyncio
    async def test_not_found(self, db):
        """Test that note_get returns error for non-existent note."""
        result = await _handle_tool("note_get", {"note_id": "nonexistent"})
        assert "not found" in result


class TestTicketCreateUpdate:
    @pytest.mark.asyncio
    async def test_create_returns_minimal(self, db, sample_data):
        """Test that ticket_create returns minimal confirmation."""
        result = await _handle_tool("ticket_create", {
            "project_id": sample_data["project"].id,
            "title": "New Ticket",
            "description": "This is a long description that should not be echoed back"
        })

        # Should be a simple string, not JSON
        assert "Created ticket:" in result
        assert "New Ticket" in result
        assert "backlog" in result
        # Should NOT contain the full description
        assert "long description" not in result

    @pytest.mark.asyncio
    async def test_update_returns_minimal(self, db, sample_data):
        """Test that ticket_update returns minimal confirmation."""
        ticket = sample_data["tickets"][0]
        result = await _handle_tool("ticket_update", {
            "ticket_id": ticket.id,
            "status": "done"
        })

        assert "Updated ticket:" in result
        assert ticket.id in result
        assert "done" in result


class TestTaskCreateUpdate:
    @pytest.mark.asyncio
    async def test_create_returns_minimal(self, db, sample_data):
        """Test that task_create returns minimal confirmation."""
        ticket = sample_data["tickets"][0]
        result = await _handle_tool("task_create", {
            "ticket_id": ticket.id,
            "title": "New Task",
            "details": "These are detailed implementation notes that should not be echoed"
        })

        assert "Created task:" in result
        assert "New Task" in result
        assert "pending" in result
        assert "detailed implementation" not in result

    @pytest.mark.asyncio
    async def test_update_returns_minimal(self, db, sample_data):
        """Test that task_update returns minimal confirmation."""
        ticket = sample_data["tickets"][0]
        tasks = db.list_tasks(ticket.id)
        task = tasks[0]

        result = await _handle_tool("task_update", {
            "task_id": task.id,
            "status": "done"
        })

        assert "Updated task:" in result
        assert task.id in result
        assert "done" in result


class TestNoteAdd:
    @pytest.mark.asyncio
    async def test_returns_minimal(self, db, sample_data):
        """Test that note_add returns minimal confirmation."""
        ticket = sample_data["tickets"][0]
        result = await _handle_tool("note_add", {
            "entity_type": "ticket",
            "entity_id": ticket.id,
            "content": "This is a very long note content that should not be echoed back to save context"
        })

        assert "Added note" in result
        assert "ticket" in result
        assert ticket.id in result
        # Should NOT contain the note content
        assert "very long note content" not in result
