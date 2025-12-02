"""Export all project tracking data to JSON format."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import DEFAULT_DB_PATH, TrackerDB


def serialize_datetime(obj: Any) -> str:
    """Convert datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def export_to_json(db: TrackerDB, output_file: Path | None = None) -> dict:
    """Export all data from the database to a JSON structure."""
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "orgs": [],
        "projects": [],
        "tickets": [],
        "tasks": [],
        "notes": [],
        "task_dependencies": [],
    }

    # Export organizations
    orgs = db.list_orgs()
    for org in orgs:
        export_data["orgs"].append(
            {
                "id": org.id,
                "name": org.name,
                "created_at": org.created_at.isoformat(),
            }
        )

    # Export projects
    projects = db.list_projects()
    for project in projects:
        export_data["projects"].append(
            {
                "id": project.id,
                "org_id": project.org_id,
                "name": project.name,
                "repo_path": project.repo_path,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
            }
        )

    # Export tickets
    tickets = db.list_tickets()
    for ticket in tickets:
        export_data["tickets"].append(
            {
                "id": ticket.id,
                "project_id": ticket.project_id,
                "title": ticket.title,
                "description": ticket.description,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "created_at": ticket.created_at.isoformat(),
                "started_at": ticket.started_at.isoformat() if ticket.started_at else None,
                "completed_at": ticket.completed_at.isoformat() if ticket.completed_at else None,
                "assignees": ticket.assignees,
                "tags": ticket.tags,
                "related_repos": ticket.related_repos,
                "acceptance_criteria": ticket.acceptance_criteria,
                "blockers": ticket.blockers,
                "metadata": ticket.metadata,
            }
        )

    # Export tasks
    tasks = db.list_tasks()
    for task in tasks:
        export_data["tasks"].append(
            {
                "id": task.id,
                "ticket_id": task.ticket_id,
                "title": task.title,
                "details": task.details,
                "status": task.status.value,
                "priority": task.priority.value,
                "complexity": task.complexity.value,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "acceptance_criteria": task.acceptance_criteria,
                "metadata": task.metadata,
            }
        )

    # Export notes
    for org in orgs:
        notes = db.get_notes("org", org.id)
        for note in notes:
            export_data["notes"].append(
                {
                    "id": note.id,
                    "entity_type": note.entity_type,
                    "entity_id": note.entity_id,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                }
            )

    for project in projects:
        notes = db.get_notes("project", project.id)
        for note in notes:
            export_data["notes"].append(
                {
                    "id": note.id,
                    "entity_type": note.entity_type,
                    "entity_id": note.entity_id,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                }
            )

    for ticket in tickets:
        notes = db.get_notes("ticket", ticket.id)
        for note in notes:
            export_data["notes"].append(
                {
                    "id": note.id,
                    "entity_type": note.entity_type,
                    "entity_id": note.entity_id,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                }
            )

    for task in tasks:
        notes = db.get_notes("task", task.id)
        for note in notes:
            export_data["notes"].append(
                {
                    "id": note.id,
                    "entity_type": note.entity_type,
                    "entity_id": note.entity_id,
                    "content": note.content,
                    "created_at": note.created_at.isoformat(),
                }
            )

    # Export task dependencies
    for task in tasks:
        dependencies = db.get_task_dependencies(task.id)
        for dep_id in dependencies:
            export_data["task_dependencies"].append(
                {
                    "task_id": task.id,
                    "depends_on_id": dep_id,
                }
            )

    # Add summary stats
    export_data["stats"] = {
        "orgs": len(export_data["orgs"]),
        "projects": len(export_data["projects"]),
        "tickets": len(export_data["tickets"]),
        "tasks": len(export_data["tasks"]),
        "notes": len(export_data["notes"]),
        "task_dependencies": len(export_data["task_dependencies"]),
    }

    # Write to file or stdout
    json_output = json.dumps(export_data, indent=2, default=serialize_datetime, ensure_ascii=False)

    if output_file:
        output_file.write_text(json_output, encoding="utf-8")
        print(
            f"Exported {export_data['stats']['orgs']} orgs, "
            f"{export_data['stats']['projects']} projects, "
            f"{export_data['stats']['tickets']} tickets, "
            f"{export_data['stats']['tasks']} tasks, "
            f"{export_data['stats']['notes']} notes to {output_file}",
            file=sys.stderr,
        )
    else:
        print(json_output)

    return export_data


def main():
    """Main entry point for the JSON export script."""
    parser = argparse.ArgumentParser(description="Export all project tracking data to JSON format")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help=f"Path to database file (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args()

    db = None
    try:
        db = TrackerDB(args.db_path) if args.db_path else TrackerDB()
        export_to_json(db, args.output)
    except Exception as e:
        print(f"Error exporting data: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if db:
            db.conn.close()


if __name__ == "__main__":
    main()
