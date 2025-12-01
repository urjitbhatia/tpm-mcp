"""Tests for migration from JSON to SQLite."""
import json
import tempfile
from pathlib import Path

import pytest

from tracker_mcp.db import TrackerDB
from tracker_mcp.migrate import migrate_from_json, extract_acceptance_criteria, extract_metadata


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
    Path(str(db_path) + "-wal").unlink(missing_ok=True)
    Path(str(db_path) + "-shm").unlink(missing_ok=True)


@pytest.fixture
def json_root(tmp_path):
    """Create a mock JSON project tracker structure."""
    # Create directory structure
    (tmp_path / "orgs" / "pimlico" / "projects" / "backend").mkdir(parents=True)
    (tmp_path / "orgs" / "pimlico" / "projects" / "frontend").mkdir(parents=True)

    # Create index.json
    index = {
        "organizations": ["pimlico"],
        "stats": {"totalFeatures": 3, "totalProjects": 2}
    }
    with open(tmp_path / "index.json", "w") as f:
        json.dump(index, f)

    # Create org-meta.json
    org_meta = {
        "name": "Pimlico",
        "description": "Test organization",
        "created": "2025-11-26"
    }
    with open(tmp_path / "orgs" / "pimlico" / "org-meta.json", "w") as f:
        json.dump(org_meta, f)

    # Create project-meta.json for backend
    project_meta = {
        "name": "Backend",
        "description": "Backend project",
        "created": "2025-11-26",
        "repos": [{"name": "backend", "path": "/path/to/backend"}]
    }
    with open(tmp_path / "orgs" / "pimlico" / "projects" / "backend" / "project-meta.json", "w") as f:
        json.dump(project_meta, f)

    # Create roadmap.json for backend
    roadmap = {
        "features": [
            {
                "id": "FEAT-001",
                "title": "Test Feature 1",
                "description": "First test feature",
                "status": "done",
                "priority": "high",
                "created": "2025-11-26",
                "completed": "2025-11-27",
                "assignees": ["Staff Engineer"],
                "tags": ["api", "backend"],
                "relatedRepos": ["pimlico"],
                "acceptanceCriteria": ["Criteria 1", "Criteria 2"],
                "blockers": [],
                "notes": ["First note", "Second note"],
                "architecture": {
                    "decision": "Use FastAPI",
                    "reasoning": ["Performance"]
                },
                "implementationPlan": {
                    "phase1": {
                        "name": "MVP",
                        "status": "completed",
                        "tasks": [
                            {
                                "id": "TASK-001-1",
                                "description": "Create API endpoints",
                                "status": "completed",
                                "completedDate": "2025-11-27",
                                "filesCreated": ["/src/routes.py"]
                            },
                            {
                                "id": "TASK-001-2",
                                "description": "Add tests",
                                "status": "completed",
                                "completedDate": "2025-11-27"
                            }
                        ]
                    }
                }
            },
            {
                "id": "FEAT-002",
                "title": "Test Feature 2",
                "description": "Second test feature",
                "status": "in-progress",
                "priority": "medium",
                "created": "2025-11-27",
                "started": "2025-11-28",
                "subTasks": [
                    {
                        "id": "SUBTASK-002-1",
                        "title": "Subtask 1",
                        "status": "done",
                        "priority": "high"
                    },
                    {
                        "id": "SUBTASK-002-2",
                        "title": "Subtask 2",
                        "status": "pending",
                        "priority": "medium"
                    }
                ]
            },
            {
                "id": "ISSUE-001",
                "title": "Bug Fix",
                "description": "Fix a bug",
                "status": "completed",
                "priority": "critical"
            }
        ]
    }
    with open(tmp_path / "orgs" / "pimlico" / "projects" / "backend" / "roadmap.json", "w") as f:
        json.dump(roadmap, f)

    # Create project-meta.json for frontend
    project_meta = {
        "name": "Frontend",
        "description": "Frontend project",
        "created": "2025-11-26"
    }
    with open(tmp_path / "orgs" / "pimlico" / "projects" / "frontend" / "project-meta.json", "w") as f:
        json.dump(project_meta, f)

    # Create roadmap.json for frontend
    roadmap = {
        "features": [
            {
                "id": "FEAT-FE-001",
                "title": "URL Navigation",
                "status": "done",
                "priority": "high",
                "acceptanceCriteria": {
                    "phase1": ["URL updates", "Back button works"],
                    "phase2": ["Deep links", "Bookmarks"]
                }
            }
        ]
    }
    with open(tmp_path / "orgs" / "pimlico" / "projects" / "frontend" / "roadmap.json", "w") as f:
        json.dump(roadmap, f)

    return tmp_path


class TestExtractHelpers:
    def test_extract_acceptance_criteria_list(self):
        feature = {"acceptanceCriteria": ["Criteria 1", "Criteria 2"]}
        result = extract_acceptance_criteria(feature)
        assert result == ["Criteria 1", "Criteria 2"]

    def test_extract_acceptance_criteria_dict(self):
        feature = {
            "acceptanceCriteria": {
                "phase1": ["P1 Criteria 1", "P1 Criteria 2"],
                "phase2": ["P2 Criteria 1"]
            }
        }
        result = extract_acceptance_criteria(feature)
        assert len(result) == 3
        assert "[phase1] P1 Criteria 1" in result
        assert "[phase2] P2 Criteria 1" in result

    def test_extract_acceptance_criteria_none(self):
        feature = {}
        result = extract_acceptance_criteria(feature)
        assert result is None

    def test_extract_metadata(self):
        feature = {
            "architecture": {"decision": "Test"},
            "implementationPlan": {"phase1": {}},
            "title": "Should not be in metadata"
        }
        result = extract_metadata(feature)
        assert "architecture" in result
        assert "implementationPlan" in result
        assert "title" not in result


class TestMigration:
    def test_migrate_creates_org(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        assert stats["orgs"] == 1
        orgs = db.list_orgs()
        assert len(orgs) == 1
        assert orgs[0].name == "Pimlico"

    def test_migrate_creates_projects(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        assert stats["projects"] == 2
        projects = db.list_projects()
        assert len(projects) == 2
        names = {p.name for p in projects}
        assert "Backend" in names
        assert "Frontend" in names

    def test_migrate_creates_features(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        assert stats["features"] == 4  # 3 in backend + 1 in frontend
        features = db.list_features()
        assert len(features) == 4

        # Check specific feature
        feat1 = db.get_feature("FEAT-001")
        assert feat1 is not None
        assert feat1.title == "Test Feature 1"
        assert feat1.status.value == "done"
        assert feat1.priority.value == "high"
        assert feat1.assignees == ["Staff Engineer"]
        assert feat1.tags == ["api", "backend"]
        assert feat1.acceptance_criteria == ["Criteria 1", "Criteria 2"]
        assert feat1.metadata is not None
        assert "architecture" in feat1.metadata

    def test_migrate_creates_tasks_from_implementation_plan(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        # Check tasks from implementationPlan
        task1 = db.get_task("TASK-001-1")
        assert task1 is not None
        assert task1.title == "Create API endpoints"
        assert task1.status.value == "done"  # "completed" normalized to "done"
        assert task1.metadata is not None
        assert "filesCreated" in task1.metadata

    def test_migrate_creates_tasks_from_subtasks(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        # Check tasks from subTasks
        subtask1 = db.get_task("SUBTASK-002-1")
        assert subtask1 is not None
        assert subtask1.title == "Subtask 1"
        assert subtask1.status.value == "done"
        assert subtask1.priority.value == "high"

    def test_migrate_creates_notes(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        assert stats["notes"] == 2  # Two notes for FEAT-001
        notes = db.get_notes("feature", "FEAT-001")
        assert len(notes) == 2
        contents = {n.content for n in notes}
        assert "First note" in contents
        assert "Second note" in contents

    def test_migrate_handles_issue_ids(self, db, json_root):
        """Test that ISSUE- prefixed IDs are preserved."""
        stats = migrate_from_json(json_root, db)

        issue = db.get_feature("ISSUE-001")
        assert issue is not None
        assert issue.title == "Bug Fix"
        assert issue.priority.value == "critical"

    def test_migrate_handles_nested_acceptance_criteria(self, db, json_root):
        """Test that dict-style acceptanceCriteria is flattened."""
        stats = migrate_from_json(json_root, db)

        feat = db.get_feature("FEAT-FE-001")
        assert feat is not None
        assert feat.acceptance_criteria is not None
        assert len(feat.acceptance_criteria) == 4
        # Should have phase prefixes
        assert any("[phase1]" in c for c in feat.acceptance_criteria)
        assert any("[phase2]" in c for c in feat.acceptance_criteria)

    def test_migrate_stats_are_accurate(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        assert stats["orgs"] == 1
        assert stats["projects"] == 2
        assert stats["features"] == 4
        assert stats["tasks"] == 4  # 2 from phase1 + 2 subtasks
        assert stats["notes"] == 2
        assert len(stats["errors"]) == 0

    def test_migrate_missing_index_returns_error(self, db, tmp_path):
        stats = migrate_from_json(tmp_path, db)
        assert len(stats["errors"]) > 0
        assert "Index file not found" in stats["errors"][0]

    def test_migrate_handles_project_repo_path(self, db, json_root):
        stats = migrate_from_json(json_root, db)

        projects = db.list_projects()
        backend = next(p for p in projects if p.name == "Backend")
        assert backend.repo_path == "/path/to/backend"


class TestMigrationRealData:
    """Tests using the actual project-tracker data structure."""

    def test_migrate_real_structure_if_exists(self, db):
        """Test migration with real data if it exists."""
        real_path = Path("/Users/urjit/project-tracker")
        if not real_path.exists():
            pytest.skip("Real project-tracker not found")

        stats = migrate_from_json(real_path, db)

        # Basic sanity checks
        assert stats["orgs"] >= 1
        assert stats["projects"] >= 1
        assert stats["features"] >= 1
        assert len(stats["errors"]) == 0, f"Migration errors: {stats['errors']}"

        # Verify roadmap view works
        roadmap = db.get_roadmap()
        assert len(roadmap.orgs) >= 1
