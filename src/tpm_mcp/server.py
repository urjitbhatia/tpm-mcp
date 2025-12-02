"""MCP Server for project tracking."""
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .db import TrackerDB, DEFAULT_DB_PATH
from .models import (
    OrgCreate, ProjectCreate,
    TicketCreate, TicketUpdate, TicketStatus,
    TaskCreate, TaskUpdate, TaskStatus,
    NoteCreate, Priority, Complexity,
)

# Initialize server and database
server = Server("technical-project-manager")
db = TrackerDB()


def _json(obj) -> str:
    """Convert model to JSON string."""
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump(), default=str, indent=2)
    return json.dumps(obj, default=str, indent=2)


# --- Tool Definitions ---

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # Roadmap view - PRIMARY TOOL for checking status
        Tool(
            name="roadmap_view",
            description="""PROJECT MANAGEMENT (TPM): Get the full project roadmap showing all work status.

USE THIS TOOL WHEN:
- User asks "what's in progress?" or "what are we working on?"
- User asks "TPM status", ":TPM:" prefix, or "show me the roadmap"
- User asks about pending/blocked/completed work
- User asks "what features are we working on this sprint?"
- You need to check what features or tasks exist before updating status
- Starting a work session to see current state
- After git operations to map changes to tracked tasks
- User completes work and you need to find related tasks to mark done

This replaces the project-tracking-pm agent. Returns all organizations, projects, features (with status/priority), and their tasks.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Filter by organization ID (optional)"},
                    "format": {"type": "string", "enum": ["json", "summary"],
                              "description": "Output format: 'json' for full data, 'summary' for readable overview (default: summary)"}
                }
            }
        ),
        # Ticket operations
        Tool(
            name="ticket_create",
            description="""PROJECT MANAGEMENT (TPM): Create a new ticket, epic, or issue to track.

USE THIS TOOL WHEN:
- User says ":TPM: Add X feature to the roadmap"
- User wants to add a new feature/ticket/issue
- User says "add ticket for X" or "create feature for Y"
- Breaking down work into trackable items
- User asks to scope out or define new work
- User discusses new work that should be tracked

Use roadmap_view first to get the project_id. Tickets are high-level work items (like Jira epics/stories).""",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID (use project_list to find)"},
                    "title": {"type": "string", "description": "Ticket title"},
                    "description": {"type": "string", "description": "Detailed description of the ticket"},
                    "status": {"type": "string", "enum": ["backlog", "planned", "in-progress", "done", "blocked"],
                             "description": "Ticket status (default: backlog)"},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"],
                                "description": "Priority level (default: medium)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                    "assignees": {"type": "array", "items": {"type": "string"}, "description": "Who is working on this"}
                },
                "required": ["project_id", "title"]
            }
        ),
        Tool(
            name="ticket_update",
            description="""PROJECT MANAGEMENT (TPM): Update a ticket's status, priority, or details.

USE THIS TOOL WHEN:
- User says "I just finished implementing X" - mark related ticket as done
- User says "I've pushed commits for X" - update status based on progress
- Marking work as in-progress, done, or blocked
- Changing priority of a ticket
- User completes a ticket and needs to update status
- Adding/updating tags or assignees

Use roadmap_view first to find the ticket_id.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID (e.g., FEAT-001)"},
                    "title": {"type": "string", "description": "New title"},
                    "description": {"type": "string", "description": "New description"},
                    "status": {"type": "string", "enum": ["backlog", "planned", "in-progress", "done", "blocked"],
                             "description": "New status"},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"],
                                "description": "New priority"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Updated tags"},
                    "assignees": {"type": "array", "items": {"type": "string"}, "description": "Updated assignees"}
                },
                "required": ["ticket_id"]
            }
        ),
        Tool(
            name="ticket_list",
            description="PROJECT MANAGEMENT: List tickets filtered by project or status. Use roadmap_view for full overview.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Filter by project ID"},
                    "status": {"type": "string", "enum": ["backlog", "planned", "in-progress", "done", "blocked"],
                             "description": "Filter by status"}
                }
            }
        ),
        Tool(
            name="ticket_get",
            description="PROJECT MANAGEMENT: Get detailed info about a specific ticket including all its tasks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Ticket ID (e.g., FEAT-001)"}
                },
                "required": ["ticket_id"]
            }
        ),
        # Task operations
        Tool(
            name="task_create",
            description="""PROJECT MANAGEMENT (TPM): Create a task (sub-item) under a ticket.

USE THIS TOOL WHEN:
- Breaking down a ticket into smaller tasks
- User asks to add implementation steps
- Creating a work breakdown structure""",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Parent ticket ID"},
                    "title": {"type": "string", "description": "Task title"},
                    "details": {"type": "string", "description": "Task details/implementation notes"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "done", "blocked"],
                             "description": "Task status (default: pending)"},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"],
                                "description": "Priority (default: medium)"},
                    "complexity": {"type": "string", "enum": ["simple", "medium", "complex"],
                                  "description": "Complexity estimate (default: medium)"}
                },
                "required": ["ticket_id", "title"]
            }
        ),
        Tool(
            name="task_update",
            description="PROJECT MANAGEMENT (TPM): Update a task's status or details. Use when completing or updating task progress.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID (e.g., TASK-001-1)"},
                    "title": {"type": "string", "description": "New title"},
                    "details": {"type": "string", "description": "New details"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "done", "blocked"],
                             "description": "New status"},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"],
                                "description": "New priority"},
                    "complexity": {"type": "string", "enum": ["simple", "medium", "complex"],
                                  "description": "New complexity"}
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="task_list",
            description="PROJECT MANAGEMENT (TPM): List tasks filtered by ticket or status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Filter by ticket ID"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "done", "blocked"],
                             "description": "Filter by status"}
                }
            }
        ),
        # Notes
        Tool(
            name="note_add",
            description="PROJECT MANAGEMENT (TPM): Add a note/comment to a ticket or task for context or decisions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "enum": ["org", "project", "ticket", "task"],
                                   "description": "Type of entity"},
                    "entity_id": {"type": "string", "description": "ID of the entity"},
                    "content": {"type": "string", "description": "Note content"}
                },
                "required": ["entity_type", "entity_id", "content"]
            }
        ),
        # Org/Project operations (less frequently used)
        Tool(
            name="org_list",
            description="PROJECT MANAGEMENT: List all organizations. Usually only one org exists.",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="org_create",
            description="PROJECT MANAGEMENT: Create a new organization (rarely needed).",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Organization name"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="project_list",
            description="PROJECT MANAGEMENT: List projects in an organization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Filter by organization ID"}
                }
            }
        ),
        Tool(
            name="project_create",
            description="PROJECT MANAGEMENT: Create a new project under an organization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Organization ID"},
                    "name": {"type": "string", "description": "Project name"},
                    "repo_path": {"type": "string", "description": "Path to git repo"},
                    "description": {"type": "string", "description": "Project description"}
                },
                "required": ["org_id", "name"]
            }
        ),
        # Info tool
        Tool(
            name="info",
            description="Get information about the tracker MCP server: database location, stats, and usage.",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


# --- Tool Handlers ---

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        result = await _handle_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _handle_tool(name: str, args: dict) -> str:
    # Orgs
    if name == "org_create":
        org = db.create_org(OrgCreate(name=args["name"]))
        return f"Created org: {_json(org)}"

    if name == "org_list":
        orgs = db.list_orgs()
        return _json([o.model_dump() for o in orgs])

    # Projects
    if name == "project_create":
        project = db.create_project(ProjectCreate(
            org_id=args["org_id"],
            name=args["name"],
            repo_path=args.get("repo_path"),
            description=args.get("description")
        ))
        return f"Created project: {_json(project)}"

    if name == "project_list":
        projects = db.list_projects(args.get("org_id"))
        return _json([p.model_dump() for p in projects])

    # Tickets
    if name == "ticket_create":
        ticket = db.create_ticket(TicketCreate(
            project_id=args["project_id"],
            title=args["title"],
            description=args.get("description"),
            status=TicketStatus(args.get("status", "backlog")),
            priority=Priority(args.get("priority", "medium")),
            tags=args.get("tags"),
            assignees=args.get("assignees")
        ))
        return f"Created ticket: {_json(ticket)}"

    if name == "ticket_list":
        status = TicketStatus(args["status"]) if args.get("status") else None
        tickets = db.list_tickets(args.get("project_id"), status)
        return _json([t.model_dump() for t in tickets])

    if name == "ticket_update":
        update = TicketUpdate(
            title=args.get("title"),
            description=args.get("description"),
            status=TicketStatus(args["status"]) if args.get("status") else None,
            priority=Priority(args["priority"]) if args.get("priority") else None,
            tags=args.get("tags"),
            assignees=args.get("assignees")
        )
        ticket = db.update_ticket(args["ticket_id"], update)
        if ticket:
            return f"Updated ticket: {_json(ticket)}"
        return f"Ticket {args['ticket_id']} not found"

    if name == "ticket_get":
        ticket = db.get_ticket(args["ticket_id"])
        if not ticket:
            return f"Ticket {args['ticket_id']} not found"
        tasks = db.list_tasks(args["ticket_id"])
        return _json({
            "ticket": ticket.model_dump(),
            "tasks": [t.model_dump() for t in tasks]
        })

    # Tasks
    if name == "task_create":
        task = db.create_task(TaskCreate(
            ticket_id=args["ticket_id"],
            title=args["title"],
            details=args.get("details"),
            status=TaskStatus(args.get("status", "pending")),
            priority=Priority(args.get("priority", "medium")),
            complexity=Complexity(args.get("complexity", "medium"))
        ))
        return f"Created task: {_json(task)}"

    if name == "task_list":
        status = TaskStatus(args["status"]) if args.get("status") else None
        tasks = db.list_tasks(args.get("ticket_id"), status)
        return _json([t.model_dump() for t in tasks])

    if name == "task_update":
        update = TaskUpdate(
            title=args.get("title"),
            details=args.get("details"),
            status=TaskStatus(args["status"]) if args.get("status") else None,
            priority=Priority(args["priority"]) if args.get("priority") else None,
            complexity=Complexity(args["complexity"]) if args.get("complexity") else None
        )
        task = db.update_task(args["task_id"], update)
        if task:
            return f"Updated task: {_json(task)}"
        return f"Task {args['task_id']} not found"

    # Notes
    if name == "note_add":
        note = db.add_note(NoteCreate(
            entity_type=args["entity_type"],
            entity_id=args["entity_id"],
            content=args["content"]
        ))
        return f"Added note: {_json(note)}"

    # Roadmap view
    if name == "roadmap_view":
        roadmap = db.get_roadmap(args.get("org_id"))
        fmt = args.get("format", "summary")

        if fmt == "json":
            return _json(roadmap)

        # Summary format
        lines = ["# Roadmap Summary\n"]
        lines.append(f"**Stats**: {roadmap.stats['tickets_done']}/{roadmap.stats['total_tickets']} tickets, "
                    f"{roadmap.stats['tasks_done']}/{roadmap.stats['total_tasks']} tasks "
                    f"({roadmap.stats['completion_pct']}% complete)\n")

        for org in roadmap.orgs:
            lines.append(f"## {org.name}")
            for proj in org.projects:
                lines.append(f"\n### {proj.name}")
                if proj.description:
                    lines.append(f"_{proj.description}_\n")
                lines.append(f"Tickets: {proj.tickets_done}/{proj.ticket_count} done\n")

                for ticket in proj.tickets:
                    status_icon = {
                        "backlog": "[ ]", "planned": "[P]", "in-progress": "[~]",
                        "done": "[x]", "blocked": "[!]"
                    }.get(ticket.status.value, "[ ]")
                    prio = f"({ticket.priority.value})" if ticket.priority.value in ["critical", "high"] else ""
                    lines.append(f"- {status_icon} **{ticket.id}**: {ticket.title} {prio}")
                    lines.append(f"  Tasks: {ticket.tasks_done}/{ticket.task_count}")

                    # Show incomplete tasks
                    incomplete = [t for t in ticket.tasks if t.status.value != "done"]
                    for task in incomplete[:5]:  # Show max 5
                        t_icon = {"pending": "[ ]", "in-progress": "[~]", "blocked": "[!]"}.get(task.status.value, "[ ]")
                        lines.append(f"    - {t_icon} {task.id}: {task.title}")
                    if len(incomplete) > 5:
                        lines.append(f"    - ... and {len(incomplete) - 5} more")

        return "\n".join(lines)

    # Info
    if name == "info":
        import os
        roadmap = db.get_roadmap()
        db_size = os.path.getsize(DEFAULT_DB_PATH) if DEFAULT_DB_PATH.exists() else 0
        db_size_mb = db_size / (1024 * 1024)

        info = f"""# Tracker MCP Server

## Database
- **Location**: `{DEFAULT_DB_PATH}`
- **Size**: {db_size_mb:.2f} MB
- **Mode**: SQLite with WAL (concurrent read/write safe)

## Current Stats
- **Organizations**: {len(roadmap.orgs)}
- **Projects**: {sum(len(o.projects) for o in roadmap.orgs)}
- **Tickets**: {roadmap.stats.get('total_tickets', 0)} ({roadmap.stats.get('tickets_done', 0)} done)
- **Tasks**: {roadmap.stats.get('total_tasks', 0)} ({roadmap.stats.get('tasks_done', 0)} done)
- **Completion**: {roadmap.stats.get('completion_pct', 0)}%

## Installation

Add to Claude Code with:
```bash
claude mcp add tracker --scope user -- uv run --directory /path/to/tpm-mcp tpm-mcp
```

## Available Tools
- `roadmap_view` - Get full project roadmap
- `ticket_create/update/list/get` - Manage tickets (features, issues, epics)
- `task_create/update/list` - Manage tasks under tickets
- `note_add` - Add notes to any entity
- `org_list/create` - Manage organizations
- `project_list/create` - Manage projects
- `info` - This info page

## Migration
To import from JSON project tracker:
```bash
uv run python -m tpm_mcp.migrate /path/to/project-tracker
```
"""
        return info

    return f"Unknown tool: {name}"


async def run_server():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Run the MCP server."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
