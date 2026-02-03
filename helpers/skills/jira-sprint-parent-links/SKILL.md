---
name: jira-sprint-parent-links
description: Generate comprehensive sprint reports showing all issues with their parent and epic relationships, including strategic hierarchy visualization.
---

# Jira Sprint Parent Links Report

Generate a comprehensive report of all issues in a specific Jira sprint for a given team, including their parent epic relationships, hierarchy visualization, and strategic organization.

## Prerequisites

- Jira MCP server must be configured and connected
- Access to Jira at https://issues.redhat.com
- Valid Jira credentials with read access to the AIPCC project
- Team membership in the AIPCC project

## Usage

This skill generates comprehensive sprint reports with:
- **Hierarchy Summary**: Strategic organization by Initiatives and Features
- **Parent Epic Details**: Initiative/Feature impact with child epic counts
- **Epic Distribution**: Parent-child epic relationships
- **Complete Issue List**: All sprint issues with links and metadata
- **Clickable Jira Links**: All issue keys linked for easy navigation

When invoked with a team number and sprint name, the skill will query Jira, analyze issue relationships, fetch parent epic details, and generate a formatted markdown report.

## Implementation

### Step 1: Parse Arguments

1. Extract team number from first argument (e.g., 5800, 5801)
2. Extract sprint name from second argument (e.g., "Sprint 25", "DP Sprint 24")
3. If arguments are missing, prompt the user:
   - "What is the team number?" (e.g., 5800)
   - "What is the sprint name?" (e.g., "Sprint 25")

### Step 2: Query Sprint Issues

1. Use `mcp__jira__jira_search` tool with JQL:
   ```
   sprint = "{sprint_name}" AND project = AIPCC
   ```
2. Request fields:
   - `summary,labels,issuetype,status,assignee,updated,created,description,reporter,priority`
   - `customfield_12313140` (Parent Link)
   - `customfield_12311140` (Epic Link)
3. Set `limit` to 50 and handle pagination with `start_at` if needed
4. Collect all issues into a single list

### Step 3: Extract Epic Information

1. Identify all unique epic keys from the issues:
   - Check `customfield_12311140` field for epic links
   - Build a set of unique epic keys
2. For each epic, fetch parent epic details using `mcp__jira__jira_get_issue`:
   - Request fields: `customfield_12313140,issuetype,summary`
   - Extract parent link (`customfield_12313140`)
   - Extract issue type (to determine if parent is Initiative or Feature)
   - Extract summary/description
3. Build epic_data dictionary:
   ```python
   {
       "EPIC-123": {
           "description": "Epic description",
           "parent_key": "INIT-456",
           "parent_type": "Initiative",
           "parent_description": "Initiative description"
       }
   }
   ```

### Step 4: Generate Hierarchy Summary

1. Group epics by parent type (Initiative vs Feature)
2. Calculate total issues for each parent epic
3. Identify the dominant initiative (most issues)
4. Generate markdown sections:
   - Count of Initiatives and Features
   - Initiative Breakdown: Each initiative with child epic counts and total issues
   - Feature Breakdown: Each feature with child epic counts and total issues
5. Sort by issue count (highest priority first)
6. Include clickable Jira links: `[KEY](https://issues.redhat.com/browse/KEY)`

### Step 5: Generate Parent Epic Details

1. For each parent epic, aggregate:
   - List of child epics
   - Total issue count across all children
   - Parent type (Initiative or Feature)
   - Description
2. Sort by total impact (most issues first)
3. Generate formatted list with:
   - Parent epic key and link
   - Type classification
   - Child epic count
   - Total issue count

### Step 6: Generate Issue List Table

Create markdown table with columns:
- **Issue Key**: Linked to Jira (`[KEY](https://issues.redhat.com/browse/KEY)`)
- **Summary**: Issue title
- **Type**: Story, Bug, Epic, Task, etc.
- **Status**: New, In Progress, To Do, Closed, etc.
- **Assignee**: Username or "Unassigned"
- **Parent Link**: Parent issue key (if sub-task)
- **Epic Link**: Epic key (if belongs to epic)

### Step 7: Generate Epic Distribution

1. Count issues per epic
2. Include parent epic link for each epic (from epic_data)
3. Include description for each epic
4. Sort by issue count (descending)
5. Create markdown table with:
   - Epic Key (linked)
   - Description
   - Issue Count
   - Epic Parent Link (NEW: shows which Initiative/Feature owns each epic)

### Step 8: Generate Parent Link Summary

Calculate and display:
- Number of issues with parent links
- List explicit parent-child relationships
- Number of issues with epic links
- Number of standalone issues (no parent or epic)

### Step 9: Format and Output Report

Generate complete markdown report with sections:
1. Title: "# Sprint {sprint_name} Issues - Team {team_number}"
2. Hierarchy Summary (if parent data available)
3. Parent Epic Details (if parent data available)
4. Parent Link Summary
5. Report Summary (statistics)
6. Detailed Issue List Table
7. Epic Distribution Summary with Parent Links
8. Footer with generation timestamp

Save the report to a file: `sprint_{sprint_number}_summary.md`

### Step 10: Display Results

1. Show the generated report to the user
2. Provide the file path where it was saved
3. Include a summary message:
   - Total issues found
   - Number of epics
   - Number of parent initiatives/features
   - File location

## Output Format

The skill produces a comprehensive markdown report including:

### Hierarchy Summary
Executive-level overview showing:
- Total count of Initiatives and Features
- Dominant initiative with issue count
- Initiative Breakdown: Each initiative with child epics and total issues
- Feature Breakdown: Each feature with child epics and total issues

### Parent Epic Details
Detailed view of parent epics:
- Parent epic key with Jira link
- Type (Initiative or Feature)
- Description
- Number of child epics
- Total issues across all child epics

### Issue List Table
Complete table with all sprint issues and their relationships

### Epic Distribution
Shows epic-level summary with parent relationships

### Statistics
- Total issue count
- Epic distribution
- Parent link statistics
- Standalone issue count

## Error Handling

- **Missing Arguments**: Prompt user for team number and sprint name
- **No Issues Found**: Display message "No issues found for Sprint {sprint_name} in team {team_number}"
- **Jira API Errors**: Display error message and suggest checking credentials
- **Invalid Sprint Name**: Suggest verifying sprint name is exact (case-sensitive)
- **Missing Parent Data**: Gracefully handle epics without parent links
- **Pagination**: Automatically handle large result sets with multiple queries

## Examples

### Basic Usage
```
User: /jira-sprint-parent-links 5800 "Sprint 25"
Assistant: [Generates comprehensive report with hierarchy, parent details, and full issue list]
```

### With Different Sprint Format
```
User: /jira-sprint-parent-links 5800 "DP Sprint 24"
Assistant: [Handles different sprint naming format correctly]
```

### No Arguments
```
User: /jira-sprint-parent-links
Assistant: What is the team number? (e.g., 5800)
User: 5800
Assistant: What is the sprint name? (e.g., "Sprint 25")
User: Sprint 26
Assistant: [Generates report for team 5800, Sprint 26]
```

## Use Cases

1. **Sprint Planning**: Review sprint scope with proper hierarchy before starting
2. **Sprint Reviews**: Generate documentation of completed work with strategic context
3. **Epic Tracking**: Understand which epics and initiatives are active in a sprint
4. **Dependency Analysis**: Identify parent-child relationships for planning
5. **Stakeholder Reporting**: Create formatted sprint summaries showing strategic alignment
6. **Initiative Tracking**: See how work rolls up to major initiatives and features
