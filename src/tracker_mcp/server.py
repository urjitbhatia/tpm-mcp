"""MCP Server for project tracking."""
import json
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .db import TrackerDB
from .models import (
    OrgCreate, ProjectCreate,
    FeatureCreate, FeatureUpdate, FeatureStatus,
    TaskCreate, TaskUpdate, TaskStatus,
    NoteCreate, Priority, Complexity,
)

# Initialize server and database
server = Server("tracker-mcp")
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
        # Orgs
        Tool(
            name="org_create",
            description="Create a new organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Organization name"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="org_list",
            description="List all organizations",
            inputSchema={"type": "object", "properties": {}}
        ),
        # Projects
        Tool(
            name="project_create",
            description="Create a new project under an organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Organization ID"},
                    "name": {"type": "string", "description": "Project name"},
                    "repo_path": {"type": "string", "description": "Path to git repo (optional)"},
                    "description": {"type": "string", "description": "Project description (optional)"}
                },
                "required": ["org_id", "name"]
            }
        ),
        Tool(
            name="project_list",
            description="List projects, optionally filtered by org",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Filter by organization ID (optional)"}
                }
            }
        ),
        # Features
        Tool(
            name="feature_create",
            description="Create a new feature/epic under a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "title": {"type": "string", "description": "Feature title"},
                    "description": {"type": "string", "description": "Feature description (optional)"},
                    "status": {"type": "string", "enum": ["backlog", "planned", "in-progress", "done", "blocked"],
                             "description": "Feature status (default: backlog)"},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"],
                                "description": "Priority (default: medium)"}
                },
                "required": ["project_id", "title"]
            }
        ),
        Tool(
            name="feature_list",
            description="List features, optionally filtered by project and/or status",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Filter by project ID (optional)"},
                    "status": {"type": "string", "enum": ["backlog", "planned", "in-progress", "done", "blocked"],
                             "description": "Filter by status (optional)"}
                }
            }
        ),
        Tool(
            name="feature_update",
            description="Update a feature's status, priority, title, or description",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_id": {"type": "string", "description": "Feature ID"},
                    "title": {"type": "string", "description": "New title (optional)"},
                    "description": {"type": "string", "description": "New description (optional)"},
                    "status": {"type": "string", "enum": ["backlog", "planned", "in-progress", "done", "blocked"],
                             "description": "New status (optional)"},
                    "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"],
                                "description": "New priority (optional)"}
                },
                "required": ["feature_id"]
            }
        ),
        Tool(
            name="feature_get",
            description="Get a single feature by ID with its tasks",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_id": {"type": "string", "description": "Feature ID"}
                },
                "required": ["feature_id"]
            }
        ),
        # Tasks
        Tool(
            name="task_create",
            description="Create a new task under a feature",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_id": {"type": "string", "description": "Feature ID"},
                    "title": {"type": "string", "description": "Task title"},
                    "details": {"type": "string", "description": "Task details (optional)"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "done", "blocked"],
                             "description": "Task status (default: pending)"},
                    "complexity": {"type": "string", "enum": ["simple", "medium", "complex"],
                                  "description": "Complexity (default: medium)"}
                },
                "required": ["feature_id", "title"]
            }
        ),
        Tool(
            name="task_list",
            description="List tasks, optionally filtered by feature and/or status",
            inputSchema={
                "type": "object",
                "properties": {
                    "feature_id": {"type": "string", "description": "Filter by feature ID (optional)"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "done", "blocked"],
                             "description": "Filter by status (optional)"}
                }
            }
        ),
        Tool(
            name="task_update",
            description="Update a task's status, title, details, or complexity",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID"},
                    "title": {"type": "string", "description": "New title (optional)"},
                    "details": {"type": "string", "description": "New details (optional)"},
                    "status": {"type": "string", "enum": ["pending", "in-progress", "done", "blocked"],
                             "description": "New status (optional)"},
                    "complexity": {"type": "string", "enum": ["simple", "medium", "complex"],
                                  "description": "New complexity (optional)"}
                },
                "required": ["task_id"]
            }
        ),
        # Notes
        Tool(
            name="note_add",
            description="Add a note to an org, project, feature, or task",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "enum": ["org", "project", "feature", "task"],
                                   "description": "Type of entity to add note to"},
                    "entity_id": {"type": "string", "description": "ID of the entity"},
                    "content": {"type": "string", "description": "Note content"}
                },
                "required": ["entity_type", "entity_id", "content"]
            }
        ),
        # Roadmap view
        Tool(
            name="roadmap_view",
            description="Get a complete roadmap view with all orgs, projects, features, and tasks. Use this to see everything at a glance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "org_id": {"type": "string", "description": "Filter by organization ID (optional)"},
                    "format": {"type": "string", "enum": ["json", "summary"],
                              "description": "Output format: 'json' for full data, 'summary' for readable overview (default: summary)"}
                }
            }
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

    # Features
    if name == "feature_create":
        feature = db.create_feature(FeatureCreate(
            project_id=args["project_id"],
            title=args["title"],
            description=args.get("description"),
            status=FeatureStatus(args.get("status", "backlog")),
            priority=Priority(args.get("priority", "medium"))
        ))
        return f"Created feature: {_json(feature)}"

    if name == "feature_list":
        status = FeatureStatus(args["status"]) if args.get("status") else None
        features = db.list_features(args.get("project_id"), status)
        return _json([f.model_dump() for f in features])

    if name == "feature_update":
        update = FeatureUpdate(
            title=args.get("title"),
            description=args.get("description"),
            status=FeatureStatus(args["status"]) if args.get("status") else None,
            priority=Priority(args["priority"]) if args.get("priority") else None
        )
        feature = db.update_feature(args["feature_id"], update)
        if feature:
            return f"Updated feature: {_json(feature)}"
        return f"Feature {args['feature_id']} not found"

    if name == "feature_get":
        feature = db.get_feature(args["feature_id"])
        if not feature:
            return f"Feature {args['feature_id']} not found"
        tasks = db.list_tasks(args["feature_id"])
        return _json({
            "feature": feature.model_dump(),
            "tasks": [t.model_dump() for t in tasks]
        })

    # Tasks
    if name == "task_create":
        task = db.create_task(TaskCreate(
            feature_id=args["feature_id"],
            title=args["title"],
            details=args.get("details"),
            status=TaskStatus(args.get("status", "pending")),
            complexity=Complexity(args.get("complexity", "medium"))
        ))
        return f"Created task: {_json(task)}"

    if name == "task_list":
        status = TaskStatus(args["status"]) if args.get("status") else None
        tasks = db.list_tasks(args.get("feature_id"), status)
        return _json([t.model_dump() for t in tasks])

    if name == "task_update":
        update = TaskUpdate(
            title=args.get("title"),
            details=args.get("details"),
            status=TaskStatus(args["status"]) if args.get("status") else None,
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
        lines.append(f"**Stats**: {roadmap.stats['features_done']}/{roadmap.stats['total_features']} features, "
                    f"{roadmap.stats['tasks_done']}/{roadmap.stats['total_tasks']} tasks "
                    f"({roadmap.stats['completion_pct']}% complete)\n")

        for org in roadmap.orgs:
            lines.append(f"## {org.name}")
            for proj in org.projects:
                lines.append(f"\n### {proj.name}")
                if proj.description:
                    lines.append(f"_{proj.description}_\n")
                lines.append(f"Features: {proj.features_done}/{proj.feature_count} done\n")

                for feat in proj.features:
                    status_icon = {
                        "backlog": "[ ]", "planned": "[P]", "in-progress": "[~]",
                        "done": "[x]", "blocked": "[!]"
                    }.get(feat.status.value, "[ ]")
                    prio = f"({feat.priority.value})" if feat.priority.value in ["critical", "high"] else ""
                    lines.append(f"- {status_icon} **{feat.id}**: {feat.title} {prio}")
                    lines.append(f"  Tasks: {feat.tasks_done}/{feat.task_count}")

                    # Show incomplete tasks
                    incomplete = [t for t in feat.tasks if t.status.value != "done"]
                    for task in incomplete[:5]:  # Show max 5
                        t_icon = {"pending": "[ ]", "in-progress": "[~]", "blocked": "[!]"}.get(task.status.value, "[ ]")
                        lines.append(f"    - {t_icon} {task.id}: {task.title}")
                    if len(incomplete) > 5:
                        lines.append(f"    - ... and {len(incomplete) - 5} more")

        return "\n".join(lines)

    return f"Unknown tool: {name}"


def main():
    """Run the MCP server."""
    import asyncio
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
