---
argument-hint: <sprint-name> [options]
description: Generate comprehensive sprint summaries by analyzing JIRA sprint data, including issue breakdown, progress metrics, and team performance insights.
---

## Name
jira:sprint-summary

## Synopsis
```
/jira:sprint-summary <sprint-name> [options]
```

## Description
Generate comprehensive sprint summaries by analyzing JIRA sprint data, including issue breakdown, progress metrics, and team performance insights. This command provides data-driven insights for sprint retrospectives, stakeholder reporting, and process improvement.

## Parameters
- `sprint-name`: The exact name or identifier of the sprint (required)
- `[options]`: Optional flags for customizing output (see Options section)

## Prerequisites
- JIRA MCP server must be configured and accessible
- Appropriate JIRA permissions to access sprint and issue data
- Valid sprint name that exists in the configured JIRA instance

## Implementation

### Core Features
1. **Sprint Overview**: Retrieve basic sprint information (dates, status, goals)
2. **Issue Analysis**: Categorize and analyze all issues in the sprint by:
   - Issue type (Story, Bug, Task, Epic, etc.)
   - Status (To Do, In Progress, Done, etc.)
   - Priority levels
   - Assignee distribution
3. **Progress Metrics**: Calculate completion rates, velocity, and burndown data
4. **Team Insights**: Analyze workload distribution and individual contributions
5. **Quality Metrics**: Identify blocked issues, overdue items, and technical debt

### Error Handling
- **Missing JIRA Configuration**: If JIRA MCP server is not configured or not working, provide clear setup instructions and troubleshooting steps
- **Missing Sprint Name**: If no sprint name provided, prompt for required parameter with examples
- **Invalid Sprint**: If sprint doesn't exist, suggest similar sprint names or provide guidance on finding correct sprint identifiers
- **Permission Issues**: Handle authentication and authorization errors gracefully with actionable feedback

### Output Format
Generate a structured markdown report including:
- Executive summary with key metrics
- Sprint overview (dates, goals, team members)
- Issue breakdown tables and charts
- Progress visualization (completion rates, velocity trends)
- Risk assessment (blocked items, potential delays)
- Recommendations for sprint improvement

## Options
- `--format`: Output format (markdown, json, csv) - default: markdown
- `--include-subtasks`: Include subtasks in analysis - default: false
- `--detailed`: Generate detailed issue-by-issue breakdown - default: false
- `--export`: Save summary to file with timestamp - default: false

## Usage Scenarios
- **Sprint Retrospectives**: Generate data-driven insights for team retrospective meetings
- **Stakeholder Reporting**: Create executive summaries for leadership updates
- **Performance Tracking**: Monitor team velocity and delivery consistency over time
- **Process Improvement**: Identify bottlenecks and areas for workflow optimization
- **Planning Sessions**: Use historical data to inform future sprint planning
