# Context: HTML Report Template

This document contains the HTML/CSS template structure for generating professional PDF status reports.

## Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Project Name} Status Report</title>
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
            align-items: flex-start;
            padding: 10px 0;
            border-bottom: 1px solid #f5f5f8;
        }

        .ticket-item:last-child {
            border-bottom: none;
        }

        .ticket-status {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            flex-shrink: 0;
            font-size: 14px;
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
        }

        .ticket-id {
            font-size: 0.75rem;
            color: #888;
            font-family: monospace;
        }

        .ticket-title {
            font-size: 0.95rem;
            color: #1a1a2e;
        }

        .ticket-meta {
            font-size: 0.8rem;
            color: #888;
            margin-top: 4px;
        }

        /* === Category Groups === */
        .category-group {
            margin-bottom: 16px;
        }

        .category-label {
            font-size: 0.8rem;
            color: #999;
            margin-bottom: 8px;
            padding-left: 36px;
        }

        /* === Milestones === */
        .milestone-list {
            list-style: none;
        }

        .milestone-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: #f8f9fc;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .milestone-icon {
            margin-right: 12px;
            font-size: 1.2rem;
        }

        .milestone-text {
            font-size: 0.95rem;
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
            padding: 12px 16px;
            background: white;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #e67e22;
        }

        .blocker-item .icon {
            margin-right: 12px;
            font-size: 1.1rem;
        }

        /* === Footer === */
        .footer {
            text-align: center;
            padding: 20px;
            color: #888;
            font-size: 0.85rem;
            margin-top: 30px;
            border-top: 1px solid #eee;
        }

        /* === Print Styles === */
        @media print {
            body {
                padding: 20px;
            }
            .section {
                break-inside: avoid;
            }
        }
    </style>
</head>
<body>
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
</div>
```

### Project Section
```html
<div class="section">
    <div class="section-header">
        <h2>{Project Name}</h2>
        <span class="badge">{done} / {total} Done</span>
    </div>

    <div class="subsection">
        <div class="subsection-title">Completed</div>
        <ul class="ticket-list">
            <!-- Repeat for each completed ticket -->
            <li class="ticket-item">
                <span class="ticket-status status-done">&#10003;</span>
                <div class="ticket-content">
                    <span class="ticket-id">{TICKET-ID}</span>
                    <div class="ticket-title">{Ticket Title}</div>
                    <div class="ticket-meta">{Optional metadata}</div>
                </div>
            </li>
        </ul>
    </div>

    <div class="subsection">
        <div class="subsection-title">In Progress</div>
        <ul class="ticket-list">
            <!-- Repeat for each in-progress ticket -->
            <li class="ticket-item">
                <span class="ticket-status status-progress">&#9679;</span>
                <div class="ticket-content">
                    <span class="ticket-id">{TICKET-ID}</span>
                    <div class="ticket-title">{Ticket Title}</div>
                    <div class="ticket-meta">{X}/{Y} subtasks completed</div>
                </div>
            </li>
        </ul>
    </div>
</div>
```

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
