# Context: TPM Report Overview

## Purpose

The tpm-report skill generates professional PDF status reports from tpm-mcp project tracking data. Reports are designed to be:

- **Executive-ready**: Clean, scannable format suitable for stakeholders
- **Visual**: Progress bars and status indicators for quick comprehension
- **Comprehensive**: All relevant project data in a structured layout
- **Shareable**: Self-contained PDF that can be emailed or presented

## Report Design Principles

### Information Hierarchy

1. **Overall Progress** (top) - Immediate understanding of project health
2. **Project Breakdown** - Detailed status per project
3. **Milestones** - Key achievements and in-progress work
4. **Blockers** - Risks and issues requiring attention

### Visual Design

- **Gradient header**: Professional, branded appearance
- **Card-based layout**: Clear visual separation of sections
- **Progress bars**: Intuitive completion visualization
- **Status indicators**: Color-coded checkmarks and circles
- **Consistent typography**: System fonts for cross-platform compatibility

## Report Sections

### 1. Header
- Project/Organization name
- Report generation date
- Gradient background for visual impact

### 2. Progress Overview
Two-column grid showing:
- Tickets completed (X/Y with percentage)
- Tasks completed (X/Y with percentage)
- Visual progress bars for each

### 3. Project Sections
For each project:
- Project name with completion badge
- **Completed**: Grouped by category (optional)
- **In Progress**: With task progress indicators
- **High Priority Backlog**: Upcoming important work

### 4. Key Milestones
Bulleted list of significant achievements:
- Completed milestones (green checkmark)
- In-progress milestones (yellow circle)
- Planned milestones (empty circle)

### 5. Blockers & Risks
Warning-styled section highlighting:
- Blocked tickets with descriptions
- External dependencies
- Known risks

### 6. Footer
- Generation timestamp
- Organization name

## Data Mapping

| tpm-mcp Field | Report Display |
|---------------|----------------|
| `ticket.status == "done"` | Completed section, green checkmark |
| `ticket.status == "in-progress"` | In Progress section, yellow circle |
| `ticket.status == "blocked"` | Blockers section, warning icon |
| `ticket.status == "backlog"` | Backlog section (high priority only) |
| `ticket.priority == "critical"` | Highlighted in backlog |
| `task_count / tasks_done` | Task progress indicator |
| `ticket.tags` | Category grouping (optional) |

## Customization Options

### Content Filters
- **Project filter**: Report on single project vs all
- **Backlog inclusion**: Show all backlog or high-priority only
- **Task details**: Include task breakdowns or ticket-level only

### Visual Customization
- **Brand colors**: Modify CSS gradient and accent colors
- **Logo**: Add organization logo to header
- **Footer text**: Custom attribution or branding

### Output Options
- **PDF**: Primary output via Playwright
- **HTML**: Intermediate format, can be kept for editing
- **Filename**: Default `Project-Status-{date}.pdf`

## Prerequisites

### Required
- **tpm-mcp server**: Provides `roadmap_view` tool for data

### Recommended
- **Playwright MCP**: For automatic HTML → PDF conversion
- Without Playwright: Manual browser Print → Save as PDF

## Usage Examples

### Basic Report
```
User: "Generate a project status report"
Claude: [Fetches roadmap, generates HTML, converts to PDF]
Result: Project-Status-2025-12-02.pdf
```

### Filtered Report
```
User: "Generate a report for just the backend project"
Claude: [Fetches roadmap, filters to backend, generates PDF]
Result: Backend-Status-2025-12-02.pdf
```

### Without Playwright
```
User: "Create a status report"
Claude: [Fetches roadmap, generates HTML]
Result: "HTML report saved to project-status-report.html.
        Open in browser and use Print → Save as PDF"
```

## Best Practices

1. **Generate regularly**: Weekly or sprint-end reports for consistency
2. **Archive reports**: Keep PDFs for historical comparison
3. **Customize for audience**: Executive summaries vs detailed breakdowns
4. **Include blockers**: Transparency builds trust
5. **Celebrate completions**: Milestones section highlights progress
