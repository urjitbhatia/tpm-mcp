"""Migration script to import existing JSON project tracker data into SQLite."""
import json
from pathlib import Path
from typing import Any, Optional

from .db import TrackerDB
from .models import NoteCreate


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def normalize_status(status: str) -> str:
    """Normalize status values to valid enum values."""
    status = status.lower().strip()
    status_map = {
        "completed": "done",
        "open": "backlog",
        "new": "backlog",
        "todo": "pending",
        "wip": "in-progress",
        "in_progress": "in-progress",
        "inprogress": "in-progress",
        "analyzed": "planned",  # Analyzed means it's been reviewed and planned
        "ready": "planned",
        "cancelled": "blocked",
        "deferred": "blocked",
    }
    return status_map.get(status, status)


def extract_acceptance_criteria(ticket: dict) -> Optional[list]:
    """Extract acceptance criteria from various locations in ticket data."""
    # Direct acceptanceCriteria array
    if "acceptanceCriteria" in ticket:
        ac = ticket["acceptanceCriteria"]
        if isinstance(ac, list):
            return ac
        elif isinstance(ac, dict):
            # Nested by phase: {phase1: [...], phase2: [...]}
            all_criteria = []
            for phase, criteria in ac.items():
                if isinstance(criteria, list):
                    all_criteria.extend([f"[{phase}] {c}" for c in criteria])
            return all_criteria if all_criteria else None
    return None


def extract_metadata(ticket: dict) -> dict:
    """Extract all rich metadata fields into a single dict."""
    metadata = {}

    # Fields to capture in metadata
    metadata_fields = [
        "architecture", "proposedStructure", "dependencies",
        "implementationConsiderations", "implementationPlan",
        "phase1Implementation", "phase2Implementation", "phase3Implementation",
        "technicalNotes", "achievements", "commits", "completionNotes",
        "progressNotes", "r2FolderStructure", "implementation",
        "backendDependencies"
    ]

    for field in metadata_fields:
        if field in ticket and ticket[field]:
            metadata[field] = ticket[field]

    return metadata if metadata else None


def extract_task_metadata(task: dict) -> dict:
    """Extract task-specific metadata."""
    metadata = {}

    metadata_fields = [
        "filesCreated", "filesModified", "files_to_modify",
        "testResults", "completionNotes", "details",
        "technical_notes", "estimated_effort", "sequence_order",
        "layer"
    ]

    for field in metadata_fields:
        if field in task and task[field]:
            metadata[field] = task[field]

    return metadata if metadata else None


def migrate_from_json(json_root: Path, db: TrackerDB) -> dict:
    """
    Migrate all data from JSON project tracker to SQLite.

    Args:
        json_root: Path to project-tracker directory (e.g., /Users/urjit/project-tracker)
        db: TrackerDB instance

    Returns:
        Migration stats
    """
    stats = {
        "orgs": 0,
        "projects": 0,
        "tickets": 0,
        "tasks": 0,
        "notes": 0,
        "errors": []
    }

    # Load index
    index_path = json_root / "index.json"
    if not index_path.exists():
        stats["errors"].append(f"Index file not found: {index_path}")
        return stats

    index = load_json(index_path)

    # Iterate over organizations
    orgs_dir = json_root / "orgs"
    if not orgs_dir.exists():
        stats["errors"].append(f"Orgs directory not found: {orgs_dir}")
        return stats

    for org_dir in orgs_dir.iterdir():
        if not org_dir.is_dir():
            continue

        # Load org metadata
        org_meta_path = org_dir / "org-meta.json"
        if org_meta_path.exists():
            org_meta = load_json(org_meta_path)
        else:
            org_meta = {"name": org_dir.name}

        # Create org (use directory name as ID for simplicity)
        org_id = org_dir.name.lower().replace(" ", "-")
        try:
            db.create_org_with_id(
                id=org_id,
                name=org_meta.get("name", org_dir.name),
                created_at=org_meta.get("created")
            )
            stats["orgs"] += 1
        except Exception as e:
            stats["errors"].append(f"Failed to create org {org_id}: {e}")
            continue

        # Iterate over projects
        projects_dir = org_dir / "projects"
        if not projects_dir.exists():
            continue

        for proj_dir in projects_dir.iterdir():
            if not proj_dir.is_dir():
                continue

            # Load project metadata
            proj_meta_path = proj_dir / "project-meta.json"
            if proj_meta_path.exists():
                proj_meta = load_json(proj_meta_path)
            else:
                proj_meta = {"name": proj_dir.name}

            # Get repo path if available
            repo_path = None
            if "repos" in proj_meta and proj_meta["repos"]:
                repo_path = proj_meta["repos"][0].get("path")

            # Create project
            proj_id = proj_dir.name.lower().replace(" ", "-")
            try:
                db.create_project_with_id(
                    id=proj_id,
                    org_id=org_id,
                    name=proj_meta.get("name", proj_dir.name),
                    description=proj_meta.get("description"),
                    repo_path=repo_path,
                    created_at=proj_meta.get("created")
                )
                stats["projects"] += 1
            except Exception as e:
                stats["errors"].append(f"Failed to create project {proj_id}: {e}")
                continue

            # Load roadmap
            roadmap_path = proj_dir / "roadmap.json"
            if not roadmap_path.exists():
                continue

            roadmap = load_json(roadmap_path)
            features = roadmap.get("features", [])

            for feature in features:
                ticket_id = feature.get("id")
                if not ticket_id:
                    continue

                try:
                    # Extract fields
                    acceptance_criteria = extract_acceptance_criteria(feature)
                    metadata = extract_metadata(feature)

                    db.create_ticket_with_id(
                        id=ticket_id,
                        project_id=proj_id,
                        title=feature.get("title", "Untitled"),
                        description=feature.get("description"),
                        status=normalize_status(feature.get("status", "backlog")),
                        priority=feature.get("priority", "medium"),
                        created_at=feature.get("created"),
                        started_at=feature.get("started"),
                        completed_at=feature.get("completed"),
                        assignees=feature.get("assignees"),
                        tags=feature.get("tags"),
                        related_repos=feature.get("relatedRepos"),
                        acceptance_criteria=acceptance_criteria,
                        blockers=feature.get("blockers"),
                        metadata=metadata
                    )
                    stats["tickets"] += 1

                    # Add notes
                    for note in feature.get("notes", []):
                        if isinstance(note, str) and note.strip():
                            db.add_note(NoteCreate(
                                entity_type="ticket",
                                entity_id=ticket_id,
                                content=note
                            ))
                            stats["notes"] += 1

                    # Import tasks from implementationPlan
                    impl_plan = feature.get("implementationPlan", {})
                    for phase_name, phase_data in impl_plan.items():
                        if isinstance(phase_data, dict):
                            tasks = phase_data.get("tasks", [])
                            for task in tasks:
                                task_id = task.get("id")
                                if not task_id:
                                    continue

                                task_metadata = extract_task_metadata(task)

                                db.create_task_with_id(
                                    id=task_id,
                                    ticket_id=ticket_id,
                                    title=task.get("description", task.get("title", "Untitled")),
                                    details=task.get("details"),
                                    status=normalize_status(task.get("status", "pending")),
                                    priority=task.get("priority", "medium"),
                                    completed_at=task.get("completedDate") or task.get("completed"),
                                    acceptance_criteria=task.get("acceptance_criteria"),
                                    metadata=task_metadata
                                )
                                stats["tasks"] += 1

                    # Import subTasks
                    for subtask in feature.get("subTasks", []):
                        task_id = subtask.get("id")
                        if not task_id:
                            continue

                        task_metadata = extract_task_metadata(subtask)

                        db.create_task_with_id(
                            id=task_id,
                            ticket_id=ticket_id,
                            title=subtask.get("title", subtask.get("description", "Untitled")),
                            details=subtask.get("description"),
                            status=normalize_status(subtask.get("status", "pending")),
                            priority=subtask.get("priority", "medium"),
                            completed_at=subtask.get("completed"),
                            acceptance_criteria=subtask.get("acceptance_criteria"),
                            metadata=task_metadata
                        )
                        stats["tasks"] += 1

                except Exception as e:
                    stats["errors"].append(f"Failed to create ticket {ticket_id}: {e}")
                    continue

            # Also check for separate subtask files like FEAT-007-subtasks.json
            for subtask_file in proj_dir.glob("*-subtasks.json"):
                try:
                    subtask_data = load_json(subtask_file)
                    ticket_id = subtask_data.get("feature_id")

                    if not ticket_id:
                        continue

                    # Check if ticket exists (might not if it failed to create)
                    if not db.get_ticket(ticket_id):
                        stats["errors"].append(f"Ticket {ticket_id} not found for subtask file {subtask_file}")
                        continue

                    for subtask in subtask_data.get("subtasks", []):
                        task_id = subtask.get("id")
                        if not task_id:
                            continue

                        task_metadata = extract_task_metadata(subtask)

                        db.create_task_with_id(
                            id=task_id,
                            ticket_id=ticket_id,
                            title=subtask.get("title", "Untitled"),
                            details=subtask.get("description"),
                            status=normalize_status(subtask.get("status", "pending")),
                            priority=subtask.get("priority", "medium"),
                            completed_at=subtask.get("completed"),
                            acceptance_criteria=subtask.get("acceptance_criteria"),
                            metadata=task_metadata
                        )
                        stats["tasks"] += 1

                except Exception as e:
                    stats["errors"].append(f"Failed to process subtask file {subtask_file}: {e}")

    return stats


def main():
    """Run migration from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate JSON project tracker to SQLite")
    parser.add_argument("json_root", type=Path, help="Path to project-tracker directory")
    parser.add_argument("--db-path", type=Path, help="Custom database path")
    args = parser.parse_args()

    db = TrackerDB(args.db_path) if args.db_path else TrackerDB()
    stats = migrate_from_json(args.json_root, db)

    print("\n=== Migration Complete ===")
    print(f"Organizations: {stats['orgs']}")
    print(f"Projects: {stats['projects']}")
    print(f"Tickets: {stats['tickets']}")
    print(f"Tasks: {stats['tasks']}")
    print(f"Notes: {stats['notes']}")

    if stats["errors"]:
        print(f"\nErrors ({len(stats['errors'])}):")
        for error in stats["errors"][:10]:
            print(f"  - {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")


if __name__ == "__main__":
    main()
