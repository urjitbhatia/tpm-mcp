# Workflow: Generate PDF Status Report

Generate a professional PDF status report from tpm-mcp project tracking data.

## Instructions

### 1. Fetch Roadmap Data

Call the `roadmap_view` MCP tool with `format: json` to get structured project data:

```
roadmap_view(format="json")
```

This returns all organizations, projects, tickets, and tasks with their statuses.

### 2. Extract Key Metrics

From the JSON response, calculate:
- **Overall completion**: `tickets_done / total_tickets` as percentage
- **Task completion**: `tasks_done / total_tasks` as percentage
- **Per-project stats**: Group tickets by project, count by status
- **In-progress items**: Filter tickets where `status == "in-progress"`
- **Blockers**: Filter tickets where `status == "blocked"` or have blockers

### 3. Generate HTML Report

Create an HTML file using the template structure from `context/html-template.md`.

Key sections to include:
1. **Header**: Project name and date
2. **Progress Overview**: Visual progress bars for tickets and tasks
3. **Per-Project Breakdown**:
   - Completed items (grouped by category if possible)
   - In-progress items with task counts
   - High-priority backlog
4. **Key Milestones**: Major completed items
5. **Blockers & Risks**: Any blocked items or external dependencies
6. **Footer**: Generation date

### 4. Write HTML to Temp File

Save the HTML to a temporary file in the project directory:
```
{project_root}/project-status-report.html
```

### 5. Convert to PDF with Playwright

If Playwright MCP is available:

IMPORTANT: Use it in headless mode if possible otherwise default to normal mode.

```javascript
// Navigate to the HTML file
browser_navigate(url="file://{absolute_path_to_html}")

// Generate PDF
browser_run_code(code=`
await page.pdf({
  path: '{output_path}/Project-Status-{date}.pdf',
  format: 'A4',
  printBackground: true,
  margin: { top: '20px', bottom: '20px', left: '20px', right: '20px' }
});
`)
```

### 6. Clean Up (Optional)

Remove the temporary HTML file if not needed (Ask the user for confirmation):
```
rm {project_root}/project-status-report.html
```

Or keep it for future edits.

## Expected Inputs

- **Project filter** (optional): Specific project ID to report on
- **Output path** (optional): Where to save the PDF (defaults to current directory)
- **Include backlog** (optional): Whether to include backlog items (default: high-priority only)

## Expected Outputs

- **PDF file**: `Project-Status-{YYYY-MM-DD}.pdf` in the specified output directory
- **HTML file** (optional): The intermediate HTML if kept

## Customization Options

### Filter by Project
To generate a report for a single project, filter the roadmap data before generating HTML.

### Exclude Sections
Skip sections by not including them in the HTML:
- Set `include_backlog: false` to hide backlog items
- Set `include_tasks: false` to show only ticket-level progress

### Custom Styling
Modify the CSS variables in the HTML template:
- `--color-primary`: Header gradient start
- `--color-secondary`: Header gradient end
- `--color-done`: Completed item indicator
- `--color-progress`: In-progress indicator

## Error Handling

### If Playwright is not available:
1. Generate and save the HTML file
2. Inform user: "HTML report generated at {path}. Open in browser and use Print → Save as PDF"

### If roadmap_view returns empty:
1. Check if tpm-mcp is running
2. Verify database has data with `info` tool
3. Return helpful error message

## Example Usage

**User**: "Generate a project status report"

**Claude**:
1. Calls `roadmap_view(format="json")`
2. Processes data and generates HTML
3. Uses Playwright to convert to PDF
4. Returns: "PDF report generated: `/path/to/Project-Status-2025-12-02.pdf`"
