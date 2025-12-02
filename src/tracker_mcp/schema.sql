-- Project Tracker Schema
-- SQLite with WAL mode for concurrent access

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- Organizations
CREATE TABLE IF NOT EXISTS orgs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Projects belong to an org
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    repo_path TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(org_id, name)
);

-- Tickets are trackable work items (issues, epics, features, stories)
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'backlog' CHECK(status IN ('backlog', 'planned', 'in-progress', 'done', 'blocked', 'completed')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('critical', 'high', 'medium', 'low')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    -- Rich metadata fields
    assignees TEXT,           -- JSON array: ["Staff Engineer", "TPM"]
    tags TEXT,                -- JSON array: ["slack", "integration", "api"]
    related_repos TEXT,       -- JSON array: ["pimlico", "web"]
    acceptance_criteria TEXT, -- JSON array: ["Criteria 1", "Criteria 2"]
    blockers TEXT,            -- JSON array: ["Blocker 1"]
    metadata TEXT             -- JSON blob for all other rich data (implementation, architecture, phases, etc.)
);

-- Tasks are sub-items of tickets
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    details TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'in-progress', 'done', 'blocked', 'completed')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('critical', 'high', 'medium', 'low')),
    complexity TEXT DEFAULT 'medium' CHECK(complexity IN ('simple', 'medium', 'complex')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    -- Rich metadata fields
    acceptance_criteria TEXT, -- JSON array: ["Criteria 1", "Criteria 2"]
    metadata TEXT             -- JSON blob for files_created, files_modified, test_results, technical_notes, estimated_effort, etc.
);

-- Task dependencies
CREATE TABLE IF NOT EXISTS task_dependencies (
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, depends_on_id)
);

-- Notes/comments on any item
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('org', 'project', 'ticket', 'task')),
    entity_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(org_id);
CREATE INDEX IF NOT EXISTS idx_tickets_project ON tickets(project_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tasks_ticket ON tasks(ticket_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_notes_entity ON notes(entity_type, entity_id);
