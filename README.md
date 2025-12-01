# tracker-mcp

Fast local project tracking MCP server with SQLite.

## Features

- SQLite backend with WAL mode for concurrent access
- Sub-millisecond queries
- Full CRUD for orgs, projects, features, and tasks
- Rich metadata support (tags, assignees, acceptance criteria, etc.)
- `roadmap_view` for at-a-glance overview
- Migration tool to import from JSON project tracker

## Installation

```bash
cd tracker-mcp
uv venv
uv pip install -e ".[dev]"  # Include dev dependencies for testing
```

## Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "tracker": {
      "command": "uv",
      "args": ["run", "--directory", "/Users/urjit/code/pimlico/tracker-mcp", "tracker-mcp"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `org_create` | Create organization |
| `org_list` | List organizations |
| `project_create` | Create project under org |
| `project_list` | List projects |
| `feature_create` | Create feature/epic with tags, assignees, etc. |
| `feature_list` | List features (filter by project/status) |
| `feature_update` | Update feature status/priority/metadata |
| `feature_get` | Get feature with tasks |
| `task_create` | Create task under feature |
| `task_list` | List tasks (filter by feature/status) |
| `task_update` | Update task status |
| `note_add` | Add note to any entity |
| `roadmap_view` | Full roadmap at a glance |

## Database Location

`~/.local/share/tracker-mcp/tracker.db`

## Migration from JSON

If you have existing JSON project tracker data:

```bash
# Run migration
uv run tracker-migrate /path/to/project-tracker

# Or programmatically
from tracker_mcp.migrate import migrate_from_json
from tracker_mcp.db import TrackerDB
from pathlib import Path

db = TrackerDB()
stats = migrate_from_json(Path("/path/to/project-tracker"), db)
print(f"Migrated {stats['features']} features, {stats['tasks']} tasks")
```

## Example Usage

```
# Create org and project
mcp__tracker__org_create(name="pimlico")
mcp__tracker__project_create(org_id="abc123", name="backend")

# Create feature with metadata
mcp__tracker__feature_create(
    project_id="xyz",
    title="Slack Integration",
    priority="high",
    tags=["api", "slack"],
    assignees=["Staff Engineer"]
)

# Create task
mcp__tracker__task_create(feature_id="FEAT-abc", title="Implement webhook")

# View roadmap
mcp__tracker__roadmap_view(format="summary")
```

## Testing

```bash
uv run pytest tests/ -v
```
