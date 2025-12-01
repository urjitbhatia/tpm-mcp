"""Tests for database operations."""
import json
import tempfile
from pathlib import Path

import pytest

from tracker_mcp.db import TrackerDB
from tracker_mcp.models import (
    OrgCreate, ProjectCreate, FeatureCreate, FeatureUpdate,
    TaskCreate, TaskUpdate, NoteCreate,
    FeatureStatus, TaskStatus, Priority, Complexity
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


class TestFeatures:
    def test_create_feature(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        feature = db.create_feature(FeatureCreate(
            project_id=project.id,
            title="Test Feature",
            description="A test feature",
            status=FeatureStatus.PLANNED,
            priority=Priority.HIGH,
            tags=["test", "feature"],
            assignees=["Staff Engineer"]
        ))

        assert feature.id.startswith("FEAT-")
        assert feature.title == "Test Feature"
        assert feature.status == FeatureStatus.PLANNED
        assert feature.priority == Priority.HIGH
        assert feature.tags == ["test", "feature"]
        assert feature.assignees == ["Staff Engineer"]

    def test_create_feature_with_id(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")

        feature = db.create_feature_with_id(
            id="FEAT-001",
            project_id=project.id,
            title="Test Feature",
            status="in-progress",
            priority="high",
            tags=["api", "backend"],
            metadata={"architecture": {"decision": "Use FastAPI"}}
        )

        assert feature.id == "FEAT-001"
        assert feature.status == FeatureStatus.IN_PROGRESS
        assert feature.tags == ["api", "backend"]
        assert feature.metadata == {"architecture": {"decision": "Use FastAPI"}}

    def test_feature_status_normalization(self, db):
        """Test that 'completed' status is normalized to 'done'."""
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")

        feature = db.create_feature_with_id(
            id="FEAT-001",
            project_id=project.id,
            title="Test Feature",
            status="completed"  # Should be normalized to "done"
        )

        assert feature.status == FeatureStatus.DONE

    def test_update_feature(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        feature = db.create_feature(FeatureCreate(
            project_id=project.id,
            title="Test Feature"
        ))

        updated = db.update_feature(feature.id, FeatureUpdate(
            title="Updated Feature",
            status=FeatureStatus.IN_PROGRESS,
            tags=["updated"]
        ))

        assert updated.title == "Updated Feature"
        assert updated.status == FeatureStatus.IN_PROGRESS
        assert updated.started_at is not None  # Should be set when status changes to in-progress
        assert updated.tags == ["updated"]

    def test_list_features_by_status(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))

        db.create_feature(FeatureCreate(project_id=project.id, title="Feature 1", status=FeatureStatus.BACKLOG))
        db.create_feature(FeatureCreate(project_id=project.id, title="Feature 2", status=FeatureStatus.IN_PROGRESS))
        db.create_feature(FeatureCreate(project_id=project.id, title="Feature 3", status=FeatureStatus.DONE))

        in_progress = db.list_features(status=FeatureStatus.IN_PROGRESS)
        assert len(in_progress) == 1
        assert in_progress[0].title == "Feature 2"


class TestTasks:
    def test_create_task(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        feature = db.create_feature(FeatureCreate(project_id=project.id, title="Test Feature"))

        task = db.create_task(TaskCreate(
            feature_id=feature.id,
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
        feature = db.create_feature_with_id(id="FEAT-001", project_id=project.id, title="Test Feature")

        task = db.create_task_with_id(
            id="TASK-001-1",
            feature_id=feature.id,
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
        feature = db.create_feature(FeatureCreate(project_id=project.id, title="Test Feature"))

        task1 = db.create_task(TaskCreate(feature_id=feature.id, title="Task 1"))
        task2 = db.create_task(TaskCreate(feature_id=feature.id, title="Task 2"))
        task3 = db.create_task(TaskCreate(feature_id=feature.id, title="Task 3"))

        # IDs should be sequential
        assert "-1" in task1.id
        assert "-2" in task2.id
        assert "-3" in task3.id

    def test_update_task_sets_completed_at(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        feature = db.create_feature(FeatureCreate(project_id=project.id, title="Test Feature"))
        task = db.create_task(TaskCreate(feature_id=feature.id, title="Test Task"))

        assert task.completed_at is None

        updated = db.update_task(task.id, TaskUpdate(status=TaskStatus.DONE))
        assert updated.completed_at is not None

    def test_task_dependencies(self, db):
        org = db.create_org(OrgCreate(name="Test Org"))
        project = db.create_project(ProjectCreate(org_id=org.id, name="Test Project"))
        feature = db.create_feature(FeatureCreate(project_id=project.id, title="Test Feature"))

        task1 = db.create_task(TaskCreate(feature_id=feature.id, title="Task 1"))
        task2 = db.create_task(TaskCreate(feature_id=feature.id, title="Task 2"))

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
        feature = db.create_feature(FeatureCreate(
            project_id=project.id,
            title="Test Feature",
            status=FeatureStatus.IN_PROGRESS,
            tags=["api"]
        ))
        db.create_task(TaskCreate(feature_id=feature.id, title="Task 1", status=TaskStatus.DONE))
        db.create_task(TaskCreate(feature_id=feature.id, title="Task 2", status=TaskStatus.PENDING))

        roadmap = db.get_roadmap()

        assert len(roadmap.orgs) == 1
        assert roadmap.orgs[0].name == "Test Org"
        assert len(roadmap.orgs[0].projects) == 1
        assert len(roadmap.orgs[0].projects[0].features) == 1
        assert roadmap.orgs[0].projects[0].features[0].tags == ["api"]
        assert roadmap.orgs[0].projects[0].features[0].tasks_done == 1
        assert roadmap.orgs[0].projects[0].features[0].task_count == 2

        assert roadmap.stats["total_features"] == 1
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


class TestJsonSerialization:
    def test_feature_with_complex_metadata(self, db):
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

        feature = db.create_feature_with_id(
            id="FEAT-001",
            project_id=project.id,
            title="Test Feature",
            metadata=complex_metadata
        )

        # Fetch and verify
        fetched = db.get_feature("FEAT-001")
        assert fetched.metadata == complex_metadata
        assert fetched.metadata["architecture"]["reasoning"] == ["Performance", "Async support"]

    def test_task_with_files_metadata(self, db):
        org = db.create_org_with_id(id="test-org", name="Test Org")
        project = db.create_project_with_id(id="test-project", org_id=org.id, name="Test Project")
        feature = db.create_feature_with_id(id="FEAT-001", project_id=project.id, title="Test Feature")

        task_metadata = {
            "filesCreated": ["/src/new_file.py"],
            "filesModified": ["/src/existing.py"],
            "testResults": {"passed": 10, "failed": 0, "coverage": 95.5}
        }

        task = db.create_task_with_id(
            id="TASK-001-1",
            feature_id=feature.id,
            title="Test Task",
            metadata=task_metadata
        )

        fetched = db.get_task("TASK-001-1")
        assert fetched.metadata == task_metadata
        assert fetched.metadata["testResults"]["coverage"] == 95.5
