# Context: HTML Report Template

This document contains the HTML/CSS template structure for generating professional PDF status reports.

## Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Project Name} Status Report {Month Day, Year} | {Organization Name}</title>
    <style>
        /* === Base Styles === */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #1a1a2e;
            background: #ffffff;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
        }

        /* === Header === */
        .header {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            color: white;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .header .date {
            font-size: 1rem;
            opacity: 0.9;
        }

        /* === Progress Section === */
        .progress-section {
            background: #f8f9fc;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }

        .progress-section h2 {
            font-size: 1.1rem;
            color: #667eea;
            margin-bottom: 20px;
        }

        .progress-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .progress-item {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }

        .progress-item .label {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 8px;
        }

        .progress-item .stats {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 10px;
        }

        .progress-item .percentage {
            font-size: 1rem;
            color: #667eea;
            font-weight: 600;
        }

        .progress-bar-container {
            background: #e8e8f0;
            border-radius: 10px;
            height: 12px;
            overflow: hidden;
            margin-top: 10px;
        }

        .progress-bar {
            height: 100%;
            border-radius: 10px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }

        /* === Status Summary === */
        .status-summary {
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-top: 20px;
            padding-top: 16px;
            border-top: 1px solid #e8e8f0;
        }

        .status-summary .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: #666;
        }

        .status-summary .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

        .status-summary .status-dot.done { background: #28a745; }
        .status-summary .status-dot.progress { background: #ffc107; }
        .status-summary .status-dot.backlog { background: #6c757d; }

        .status-summary .status-count {
            font-weight: 600;
            color: #1a1a2e;
        }

        /* === Section Cards === */
        .section {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            border: 1px solid #eef0f5;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #f0f0f5;
        }

        .section-header h2 {
            font-size: 1.3rem;
            color: #1a1a2e;
        }

        .section-header .badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* === Subsections === */
        .subsection {
            margin-bottom: 20px;
        }

        .subsection:last-child {
            margin-bottom: 0;
        }

        .subsection-title {
            font-size: 0.9rem;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* === Ticket List === */
        .ticket-list {
            list-style: none;
        }

        .ticket-item {
            display: flex;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f5f5f8;
        }

        .ticket-item:last-child {
            border-bottom: none;
        }

        .ticket-status {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            flex-shrink: 0;
            font-size: 12px;
        }

        .status-done {
            background: #d4edda;
            color: #28a745;
        }

        .status-progress {
            background: #fff3cd;
            color: #ffc107;
        }

        .status-backlog {
            background: #e8e8f0;
            color: #666;
        }

        .ticket-content {
            flex: 1;
            display: flex;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 6px;
        }

        .ticket-id {
            font-size: 0.75rem;
            color: #888;
            font-family: monospace;
            background: #f5f5f8;
            padding: 2px 6px;
            border-radius: 4px;
        }

        .ticket-title {
            font-size: 0.9rem;
            color: #1a1a2e;
        }

        .ticket-meta {
            font-size: 0.8rem;
            color: #888;
            width: 100%;
            padding-left: 0;
        }

        .priority-critical {
            color: #dc3545;
            font-weight: 600;
        }

        .priority-high {
            color: #fd7e14;
        }

        /* === Milestones === */
        .milestone-list {
            list-style: none;
        }

        .milestone-item {
            display: flex;
            align-items: center;
            padding: 10px 14px;
            background: #f8f9fc;
            border-radius: 8px;
            margin-bottom: 8px;
        }

        .milestone-item:last-child {
            margin-bottom: 0;
        }

        .milestone-icon {
            margin-right: 10px;
            font-size: 1rem;
        }

        .milestone-text {
            font-size: 0.9rem;
            color: #1a1a2e;
        }

        /* === Blockers === */
        .blocker-section {
            background: #fff8f0;
            border: 1px solid #ffe0b0;
        }

        .blocker-section .section-header h2 {
            color: #e67e22;
        }

        .blocker-item {
            display: flex;
            align-items: flex-start;
            padding: 10px 14px;
            background: white;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #e67e22;
            font-size: 0.9rem;
        }

        .blocker-item:last-child {
            margin-bottom: 0;
        }

        .blocker-item .icon {
            margin-right: 10px;
            font-size: 1rem;
        }

        /* === Footer === */
        .footer {
            text-align: center;
            padding: 16px;
            color: #888;
            font-size: 0.8rem;
            margin-top: 24px;
            border-top: 1px solid #eee;
        }

        /* === Compact Mode === */
        .compact .section { padding: 16px; margin-bottom: 16px; }
        .compact .section-header { margin-bottom: 14px; padding-bottom: 10px; }
        .compact .subsection { margin-bottom: 14px; }
        .compact .ticket-item { padding: 6px 0; }
        .compact .ticket-title { font-size: 0.85rem; }
        .compact .milestone-item { padding: 8px 12px; margin-bottom: 6px; }
        .compact .blocker-item { padding: 8px 12px; margin-bottom: 6px; }
        .compact .progress-section { padding: 16px; }
        .compact .progress-item { padding: 14px; }
        .compact .header { padding: 20px; margin-bottom: 20px; }
        .compact .header h1 { font-size: 1.8rem; }

        /* === Print Styles === */
        @media print {
            body { padding: 20px; }
            .section { break-inside: avoid; }
        }
    </style>
</head>
<body>
    <!-- Add class="compact" to body for dense reports -->
    <!-- Content sections go here -->
</body>
</html>
```

## Section Templates

### Header
```html
<div class="header">
    <h1>{Project Name} Status</h1>
    <div class="date">{Month Day, Year}</div>
</div>
```

### Progress Overview
```html
<div class="progress-section">
    <h2>Overall Progress</h2>
    <div class="progress-grid">
        <div class="progress-item">
            <div class="label">Tickets Completed</div>
            <div class="stats">{done} / {total}</div>
            <div class="percentage">{percentage}% Complete</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {percentage}%"></div>
            </div>
        </div>
        <div class="progress-item">
            <div class="label">Tasks Completed</div>
            <div class="stats">{tasks_done} / {tasks_total}</div>
            <div class="percentage">{task_percentage}% Complete</div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {task_percentage}%"></div>
            </div>
        </div>
    </div>
    <!-- Status Summary replaces the chart section -->
    <div class="status-summary">
        <div class="status-item">
            <span class="status-dot done"></span>
            <span>Done: <span class="status-count">{done_count}</span></span>
        </div>
        <div class="status-item">
            <span class="status-dot progress"></span>
            <span>In Progress: <span class="status-count">{progress_count}</span></span>
        </div>
        <div class="status-item">
            <span class="status-dot backlog"></span>
            <span>Backlog: <span class="status-count">{backlog_count}</span></span>
        </div>
    </div>
</div>
```

### Project Section

**Repeat this section for each project in the TPM data.** The template is project-agnostic - iterate over all projects and generate one card per project.

```html
<!-- Repeat for each project -->
<div class="section">
    <div class="section-header">
        <h2>{Project Name}</h2>
        <span class="badge">{done} / {total} Done</span>
    </div>

    <div class="subsection">
        <div class="subsection-title">Completed ({count})</div>
        <ul class="ticket-list">
            <li class="ticket-item">
                <span class="ticket-status status-done">&#10003;</span>
                <div class="ticket-content">
                    <span class="ticket-id">{TICKET-ID}</span>
                    <span class="ticket-title">{Ticket Title}</span>
                </div>
            </li>
            <!-- For long titles, truncate with ellipsis -->
            <li class="ticket-item">
                <span class="ticket-status status-done">&#10003;</span>
                <div class="ticket-content">
                    <span class="ticket-id">{TICKET-ID}</span>
                    <span class="ticket-title">Country Reports - UI Drift from Prototype...</span>
                </div>
            </li>
        </ul>
    </div>

    <div class="subsection">
        <div class="subsection-title">In Progress ({count})</div>
        <ul class="ticket-list">
            <li class="ticket-item">
                <span class="ticket-status status-progress">&#9679;</span>
                <div class="ticket-content">
                    <span class="ticket-id">{TICKET-ID}</span>
                    <span class="ticket-title">{Ticket Title}</span>
                    <div class="ticket-meta">{X}/{Y} subtasks completed</div>
                </div>
            </li>
        </ul>
    </div>

    <div class="subsection">
        <div class="subsection-title">Backlog ({count})</div>
        <ul class="ticket-list">
            <li class="ticket-item">
                <span class="ticket-status status-backlog">&#9675;</span>
                <div class="ticket-content">
                    <span class="ticket-id">{TICKET-ID}</span>
                    <span class="ticket-title">{Ticket Title}</span>
                    <div class="ticket-meta priority-high">High Priority</div>
                </div>
            </li>
        </ul>
    </div>
</div>
```

**Guidelines:**
- List all tickets individually for consistency across projects
- Truncate long titles with ellipsis (`...`) to keep lines concise
- Include subtask counts in `.ticket-meta` when relevant

### Milestones Section
```html
<div class="section">
    <div class="section-header">
        <h2>Key Milestones</h2>
    </div>
    <ul class="milestone-list">
        <li class="milestone-item">
            <span class="milestone-icon" style="color: #28a745;">&#10003;</span>
            <span class="milestone-text">{Milestone description}</span>
        </li>
        <li class="milestone-item">
            <span class="milestone-icon" style="color: #ffc107;">&#9679;</span>
            <span class="milestone-text">{In-progress milestone}</span>
        </li>
    </ul>
</div>
```

### Blockers Section
```html
<div class="section blocker-section">
    <div class="section-header">
        <h2>Blockers & Risks</h2>
    </div>
    <div class="blocker-item">
        <span class="icon">&#9888;</span>
        <div>
            <strong>{TICKET-ID}:</strong> {Blocker description}
        </div>
    </div>
</div>
```

### Footer
```html
<div class="footer">
    Generated: {Month Day, Year} | {Organization Name}
</div>
```

## Status Icons

| Status | HTML Entity | Color Class |
|--------|-------------|-------------|
| Done | `&#10003;` (checkmark) | `status-done` |
| In Progress | `&#9679;` (filled circle) | `status-progress` |
| Backlog | `&#9675;` (empty circle) | `status-backlog` |
| Warning | `&#9888;` (warning triangle) | - |

## Compact Mode

For dense reports with many items, add `class="compact"` to the body tag:

```html
<body class="compact">
```

This reduces padding, margins, and font sizes throughout the report for a more condensed view.

## Priority Classes

Add these classes to `.ticket-meta` for priority highlighting:

| Priority | Class | Color |
|----------|-------|-------|
| Critical | `priority-critical` | Red (#dc3545) |
| High | `priority-high` | Orange (#fd7e14) |

## Customization Variables

Modify these CSS custom properties for branding:

```css
:root {
    --color-primary: #667eea;      /* Header gradient start */
    --color-secondary: #764ba2;     /* Header gradient end */
    --color-done: #28a745;          /* Completed items */
    --color-progress: #ffc107;      /* In-progress items */
    --color-blocked: #e67e22;       /* Blockers/warnings */
    --color-text: #1a1a2e;          /* Primary text */
    --color-muted: #888;            /* Secondary text */
}
```
