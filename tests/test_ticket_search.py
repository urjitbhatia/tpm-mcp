"""
Tests for ticket search functionality.

This file contains comprehensive tests for the search_tickets() method.
To integrate these tests into test_db.py, copy the TestTicketSearch class
into that file.
"""
import tempfile
from pathlib import Path

import pytest

from tpm_mcp.db import TrackerDB
from tpm_mcp.models import OrgCreate, Priority, ProjectCreate, TicketCreate, TicketStatus


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


class TestTicketSearch:
    def test_search_tickets_basic(self, db):
        """Test that search returns matching tickets."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add user authentication",
            description="Implement JWT-based authentication"
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Fix database migration",
            description="Fix issues with Alembic migrations"
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Update API documentation",
            description="Add OpenAPI specs"
        ))

        results = db.search_tickets("authentication")
        assert len(results) == 1
        assert results[0]["title"] == "Add user authentication"
        assert "id" in results[0]
        assert "snippet" in results[0]

    def test_search_tickets_partial_match(self, db):
        """Test that prefix matching works (org matches organization)."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Reorganize file structure",
            description="Clean up the organization of files"
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add feature flag",
            description="Implement feature toggles"
        ))

        results = db.search_tickets("org")
        assert len(results) >= 1
        assert any("organization" in r["snippet"].lower() or "reorganize" in r["snippet"].lower() for r in results)

    def test_search_tickets_case_insensitive(self, db):
        """Test that search is case-insensitive."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Fix API bug",
            description="Fix critical API endpoint"
        ))

        results_lower = db.search_tickets("api")
        results_upper = db.search_tickets("API")
        results_mixed = db.search_tickets("Api")

        assert len(results_lower) == len(results_upper) == len(results_mixed) == 1
        assert results_lower[0]["id"] == results_upper[0]["id"] == results_mixed[0]["id"]

    def test_search_tickets_multiple_results(self, db):
        """Test that multiple matches are returned."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add API endpoint for users",
            description="Create REST API for user management"
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Update API documentation",
            description="Document all API endpoints"
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Fix API rate limiting",
            description="Implement proper rate limiting"
        ))

        results = db.search_tickets("API")
        assert len(results) == 3
        assert all("api" in r["snippet"].lower() for r in results)

    def test_search_tickets_filter_by_project(self, db):
        """Test filtering search results by project_id."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project1 = db.create_project(ProjectCreate(org_id=org.id, name="Project 1"))
        project2 = db.create_project(ProjectCreate(org_id=org.id, name="Project 2"))

        db.create_ticket(TicketCreate(
            project_id=project1.id,
            title="Add authentication",
            description="Implement auth"
        ))
        db.create_ticket(TicketCreate(
            project_id=project2.id,
            title="Add authorization",
            description="Implement authz"
        ))

        results = db.search_tickets("auth", project_id=project1.id)
        assert len(results) == 1
        assert results[0]["project_id"] == project1.id

    def test_search_tickets_filter_by_status(self, db):
        """Test filtering search results by status."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Fix bug in API",
            status=TicketStatus.IN_PROGRESS
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Fix bug in UI",
            status=TicketStatus.DONE
        ))

        results = db.search_tickets("bug", status=TicketStatus.IN_PROGRESS)
        assert len(results) == 1
        assert results[0]["status"] == "in-progress"

    def test_search_tickets_filter_by_priority(self, db):
        """Test filtering search results by priority."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Critical security fix",
            priority=Priority.CRITICAL
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Low priority fix",
            priority=Priority.LOW
        ))

        results = db.search_tickets("fix", priority=Priority.CRITICAL)
        assert len(results) == 1
        assert results[0]["priority"] == "critical"

    def test_search_tickets_filter_by_tags(self, db):
        """Test filtering search results by tags (any match)."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add feature A",
            tags=["backend", "api"]
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add feature B",
            tags=["frontend", "ui"]
        ))
        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add feature C",
            tags=["backend", "database"]
        ))

        results = db.search_tickets("feature", tags=["backend"])
        assert len(results) == 2
        assert all(any(tag in r["tags"] for tag in ["backend"]) for r in results if r["tags"])

    def test_search_tickets_combined_filters(self, db):
        """Test combining multiple filters."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project1 = db.create_project(ProjectCreate(org_id=org.id, name="Project 1"))
        project2 = db.create_project(ProjectCreate(org_id=org.id, name="Project 2"))

        db.create_ticket(TicketCreate(
            project_id=project1.id,
            title="Fix API bug",
            status=TicketStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            tags=["backend"]
        ))
        db.create_ticket(TicketCreate(
            project_id=project1.id,
            title="Fix UI bug",
            status=TicketStatus.BACKLOG,
            priority=Priority.LOW,
            tags=["frontend"]
        ))
        db.create_ticket(TicketCreate(
            project_id=project2.id,
            title="Fix database bug",
            status=TicketStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            tags=["backend"]
        ))

        results = db.search_tickets(
            "bug",
            project_id=project1.id,
            status=TicketStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            tags=["backend"]
        )
        assert len(results) == 1
        assert results[0]["title"] == "Fix API bug"

    def test_search_tickets_no_results(self, db):
        """Test that empty list is returned when no matches found."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add feature",
            description="Implement new feature"
        ))

        results = db.search_tickets("nonexistent query string")
        assert results == []

    def test_search_tickets_limit(self, db):
        """Test that limit parameter is respected."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        for i in range(25):
            db.create_ticket(TicketCreate(
                project_id=project.id,
                title=f"Feature {i}",
                description="Implement feature"
            ))

        results = db.search_tickets("feature", limit=10)
        assert len(results) == 10

    def test_search_tickets_snippet(self, db):
        """Test that snippet contains context around the match."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Add authentication system",
            description="Implement a comprehensive JWT-based authentication system with refresh tokens"
        ))

        results = db.search_tickets("authentication")
        assert len(results) == 1
        assert "snippet" in results[0]
        # Snippet should contain the matched term and some context
        snippet = results[0]["snippet"].lower()
        assert "authentication" in snippet

    def test_search_tickets_special_characters(self, db):
        """Test graceful handling of special characters in search query."""
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_ticket(TicketCreate(
            project_id=project.id,
            title="Fix C++ compiler error",
            description="Resolve issue with g++"
        ))

        # Should not crash with special regex characters
        results = db.search_tickets("C++")
        assert isinstance(results, list)

        # Should handle quotes
        results = db.search_tickets('"authentication"')
        assert isinstance(results, list)

        # Should handle parentheses
        results = db.search_tickets("(test)")
        assert isinstance(results, list)
