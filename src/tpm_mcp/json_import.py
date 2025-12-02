"""Import project tracking data from JSON format into the database."""

import argparse
import json
import sys
from pathlib import Path

from .db import DEFAULT_DB_PATH, TrackerDB


def import_from_json(db: TrackerDB, json_file: Path, clear_first: bool = False) -> dict:
    """Import data from JSON file into the database."""
    stats = {
        "orgs": 0,
        "projects": 0,
        "tickets": 0,
        "tasks": 0,
        "notes": 0,
        "task_dependencies": 0,
        "errors": [],
    }

    # Read JSON file
    try:
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        stats["errors"].append(f"File not found: {json_file}")
        return stats
    except json.JSONDecodeError as e:
        stats["errors"].append(f"Invalid JSON: {e}")
        return stats

    # Validate JSON structure
    required_keys = ["orgs", "projects", "tickets", "tasks", "notes", "task_dependencies"]
    for key in required_keys:
        if key not in data:
            stats["errors"].append(f"Missing required key: {key}")
            return stats

    # Clear database if requested
    if clear_first:
        try:
            db.conn.execute("DELETE FROM task_dependencies")
            db.conn.execute("DELETE FROM notes")
            db.conn.execute("DELETE FROM tasks")
            db.conn.execute("DELETE FROM tickets")
            db.conn.execute("DELETE FROM projects")
            db.conn.execute("DELETE FROM orgs")
            db.conn.commit()
        except Exception as e:
            stats["errors"].append(f"Error clearing database: {e}")
            return stats

    # Import organizations
    for org_data in data.get("orgs", []):
        try:
            db.create_org_with_id(
                id=org_data["id"],
                name=org_data["name"],
                created_at=org_data.get("created_at"),
            )
            stats["orgs"] += 1
        except Exception as e:
            stats["errors"].append(f"Error importing org {org_data.get('id', 'unknown')}: {e}")

    # Import projects
    for project_data in data.get("projects", []):
        try:
            db.create_project_with_id(
                id=project_data["id"],
                org_id=project_data["org_id"],
                name=project_data["name"],
                repo_path=project_data.get("repo_path"),
                description=project_data.get("description"),
                created_at=project_data.get("created_at"),
            )
            stats["projects"] += 1
        except Exception as e:
            stats["errors"].append(
                f"Error importing project {project_data.get('id', 'unknown')}: {e}"
            )

    # Import tickets
    for ticket_data in data.get("tickets", []):
        try:
            db.create_ticket_with_id(
                id=ticket_data["id"],
                project_id=ticket_data["project_id"],
                title=ticket_data["title"],
                description=ticket_data.get("description"),
                status=ticket_data.get("status", "backlog"),
                priority=ticket_data.get("priority", "medium"),
                created_at=ticket_data.get("created_at"),
                started_at=ticket_data.get("started_at"),
                completed_at=ticket_data.get("completed_at"),
                assignees=ticket_data.get("assignees"),
                tags=ticket_data.get("tags"),
                related_repos=ticket_data.get("related_repos"),
                acceptance_criteria=ticket_data.get("acceptance_criteria"),
                blockers=ticket_data.get("blockers"),
                metadata=ticket_data.get("metadata"),
            )
            stats["tickets"] += 1
        except Exception as e:
            stats["errors"].append(
                f"Error importing ticket {ticket_data.get('id', 'unknown')}: {e}"
            )

    # Import tasks
    for task_data in data.get("tasks", []):
        try:
            db.create_task_with_id(
                id=task_data["id"],
                ticket_id=task_data["ticket_id"],
                title=task_data["title"],
                details=task_data.get("details"),
                status=task_data.get("status", "pending"),
                priority=task_data.get("priority", "medium"),
                complexity=task_data.get("complexity", "medium"),
                created_at=task_data.get("created_at"),
                completed_at=task_data.get("completed_at"),
                acceptance_criteria=task_data.get("acceptance_criteria"),
                metadata=task_data.get("metadata"),
            )
            stats["tasks"] += 1
        except Exception as e:
            stats["errors"].append(f"Error importing task {task_data.get('id', 'unknown')}: {e}")

    # Import notes
    for note_data in data.get("notes", []):
        try:
            from .models import NoteCreate

            db.add_note(
                NoteCreate(
                    entity_type=note_data["entity_type"],
                    entity_id=note_data["entity_id"],
                    content=note_data["content"],
                )
            )
            stats["notes"] += 1
        except Exception as e:
            stats["errors"].append(f"Error importing note {note_data.get('id', 'unknown')}: {e}")

    # Import task dependencies
    for dep_data in data.get("task_dependencies", []):
        try:
            success = db.add_task_dependency(
                task_id=dep_data["task_id"],
                depends_on_id=dep_data["depends_on_id"],
            )
            if success:
                stats["task_dependencies"] += 1
        except Exception as e:
            stats["errors"].append(
                f"Error importing dependency {dep_data.get('task_id', 'unknown')} -> "
                f"{dep_data.get('depends_on_id', 'unknown')}: {e}"
            )

    return stats


def main():
    """Main entry point for the JSON import script."""
    parser = argparse.ArgumentParser(
        description="Import project tracking data from JSON format into the database"
    )
    parser.add_argument(
        "json_file",
        type=Path,
        help="Path to JSON file to import",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=f"Path to database file (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before importing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate JSON file without importing",
    )

    args = parser.parse_args()

    # Validate JSON file exists
    if not args.json_file.exists():
        print(f"Error: JSON file not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    # Dry run: just validate JSON
    if args.dry_run:
        try:
            with open(args.json_file, encoding="utf-8") as f:
                data = json.load(f)
            required_keys = ["orgs", "projects", "tickets", "tasks", "notes", "task_dependencies"]
            missing = [key for key in required_keys if key not in data]
            if missing:
                print(f"Error: Missing required keys: {missing}", file=sys.stderr)
                sys.exit(1)
            print(f"✓ JSON file is valid: {args.json_file}", file=sys.stderr)
            if "stats" in data:
                print(f"  Contains: {data['stats']}", file=sys.stderr)
            sys.exit(0)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Import data
    db = None
    try:
        db = TrackerDB(args.db_path) if args.db_path else TrackerDB()
        stats = import_from_json(db, args.json_file, clear_first=args.clear)

        # Print results
        print("Imported:", file=sys.stderr)
        print(f"  - {stats['orgs']} organizations", file=sys.stderr)
        print(f"  - {stats['projects']} projects", file=sys.stderr)
        print(f"  - {stats['tickets']} tickets", file=sys.stderr)
        print(f"  - {stats['tasks']} tasks", file=sys.stderr)
        print(f"  - {stats['notes']} notes", file=sys.stderr)
        print(f"  - {stats['task_dependencies']} task dependencies", file=sys.stderr)

        if stats["errors"]:
            print(f"\nErrors ({len(stats['errors'])}):", file=sys.stderr)
            for error in stats["errors"][:10]:  # Show first 10 errors
                print(f"  - {error}", file=sys.stderr)
            if len(stats["errors"]) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error importing data: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if db:
            db.conn.close()


if __name__ == "__main__":
    main()
