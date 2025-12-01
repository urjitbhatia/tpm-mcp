# tracker-mcp

Fast local project tracking MCP server with SQLite.

## Features

- SQLite backend with WAL mode for concurrent access
- Sub-millisecond queries
- Full CRUD for orgs, projects, features, and tasks
- `roadmap_view` for at-a-glance overview

## Installation

```bash
cd tracker-mcp
uv venv
uv pip install -e .
```

## Claude Code Configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "tracker": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/tracker-mcp", "tracker-mcp"]
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
| `feature_create` | Create feature/epic |
| `feature_list` | List features (filter by project/status) |
| `feature_update` | Update feature status/priority |
| `feature_get` | Get feature with tasks |
| `task_create` | Create task under feature |
| `task_list` | List tasks (filter by feature/status) |
| `task_update` | Update task status |
| `note_add` | Add note to any entity |
| `roadmap_view` | Full roadmap at a glance |

## Database Location

`~/.local/share/tracker-mcp/tracker.db`

## Example Usage

```
# Create org and project
mcp__tracker__org_create(name="pimlico")
mcp__tracker__project_create(org_id="abc123", name="backend")

# Create feature with tasks
mcp__tracker__feature_create(project_id="xyz", title="Slack Integration", priority="high")
mcp__tracker__task_create(feature_id="FEAT-abc", title="Implement webhook")

# View roadmap
mcp__tracker__roadmap_view(format="summary")
```
