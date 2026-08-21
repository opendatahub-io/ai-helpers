---
name: jira-workitem-search
description: Search Jira tickets using JQL queries. Provides common query templates and flexible output formats. Use when user needs to find or filter tickets.
allowed-tools: Bash, AskUserQuestion, Skill
user-invocable: true
---

# Jira Workitem Search

Search for Jira tickets using JQL (Jira Query Language) queries with the `acli` CLI.

## Prerequisites

- `acli` must be installed and authenticated (`acli jira auth`)

## Implementation

### Step 1: Verify ACLi Setup

Before proceeding, verify that acli is installed and authenticated by invoking the `acli-setup-check` skill:

```
/acli-setup-check
```

If the setup check fails, stop execution and guide the user to fix the issue.

### Step 2: Determine JQL Query

1. **Direct JQL**: If the user provides a JQL query, use it as-is
2. **Natural Language**: Convert user's natural language request to JQL using templates below. **Extract project names, statuses, components, and other values from the user's request** and substitute them into the templates.
3. **Interactive**: If unclear, ask the user what they want to find

#### Input Validation

Before substituting user-provided values into JQL templates, validate and sanitize the inputs:

1. **Project keys**: Validate against pattern `[A-Z]+` (e.g., AIPCC, RHOAIENG).
2. **Status values**: Quote multi-word statuses (e.g., "In Progress", "Code Review"). Common statuses: To Do, In Progress, Code Review, Done, Blocked.
3. **Ticket keys**: Validate against pattern `[A-Z]+-[0-9]+` (e.g., AIPCC-1234).
4. **Numeric values**: Validate that N in `-<N>d` is a positive integer.
5. **Issue types**: Whitelist common types: Bug, Story, Epic, Feature, Spike, Initiative, Task.
6. **Components**: Quote multi-word components (e.g., "Wheel Package Index").

If validation fails, prompt the user with a clear error message explaining the expected format.

#### Common JQL Templates

Replace placeholders like `<PROJECT>`, `<STATUS>`, `<COMPONENT>` with actual values from the user's request or conversation context.

**My open tickets:**
```jql
assignee = currentUser() AND resolution = Unresolved ORDER BY updated DESC
```

**Team backlog for a project:**
```jql
project = <PROJECT> AND status != Done ORDER BY priority DESC, updated DESC
```
Example: `project = AIPCC AND status != Done ORDER BY priority DESC, updated DESC`

**Recent updates in a project (last N days):**
```jql
project = <PROJECT> AND updatedDate >= -<N>d ORDER BY updated DESC
```
Example: `project = RHOAIENG AND updatedDate >= -7d ORDER BY updated DESC`

**Tickets by status:**
```jql
project = <PROJECT> AND status = "<STATUS>" ORDER BY updated DESC
```
Example: `project = AIPCC AND status = "In Progress" ORDER BY updated DESC`

**Tickets by type (single):**
```jql
project = <PROJECT> AND type = <TYPE> ORDER BY updated DESC
```
Example: `project = AIPCC AND type = Feature ORDER BY updated DESC`

**Tickets by type (multiple):**
```jql
project = <PROJECT> AND type IN (<TYPE1>, <TYPE2>, ...) ORDER BY updated DESC
```
Example: `project = AIPCC AND type IN (Feature, Initiative) ORDER BY updated DESC`

**Blocked tickets:**
```jql
project = <PROJECT> AND status = Blocked ORDER BY priority DESC
```

**Tickets due soon (next 7 days):**
```jql
project = <PROJECT> AND dueDate >= now() AND dueDate <= endOfWeek() AND resolution = Unresolved ORDER BY dueDate ASC
```

**Tickets by component:**
```jql
project = <PROJECT> AND component = "<COMPONENT>" ORDER BY priority DESC
```
Example: `project = AIPCC AND component = "Wheel Package Index" ORDER BY priority DESC`

**Epics and their children:**
```jql
project = <PROJECT> AND type = Epic ORDER BY created DESC
```

**Unassigned tickets:**
```jql
project = <PROJECT> AND assignee is EMPTY AND resolution = Unresolved ORDER BY priority DESC
```

**Tickets mentioned in conversation:**
Search conversation history for ticket keys, then query:
```jql
key IN (<KEY1>, <KEY2>, ...) ORDER BY updated DESC
```
Example: `key IN (AIPCC-1234, AIPCC-5678, RHOAIENG-910) ORDER BY updated DESC`

**Tips for extracting values:**
- If user says "AIPCC backlog", use `project = AIPCC`
- If user says "in progress tickets", use `status = "In Progress"`
- If user says "last week", use `updatedDate >= -7d`
- If user says "Wheel Package Index component", use `component = "Wheel Package Index"`
- If user says "features", use `type = Feature`
- If user says "features and initiatives", use `type IN (Feature, Initiative)`
- Common ticket types: Bug, Story, Epic, Feature, Spike, Initiative, Task
- If no project specified, ask the user or search conversation context for project references

### Step 3: Execute Search

Build the JQL query from validated inputs and execute the search:

```bash
# Validate and sanitize inputs extracted from user request
PROJECT="<project-from-step-2>"
if [[ ! "$PROJECT" =~ ^[A-Z]+$ ]]; then
  echo "Error: Invalid project key format. Expected uppercase letters only (e.g., AIPCC, RHOAIENG)"
  exit 1
fi

# For status values with spaces, add quotes
STATUS="<status-from-step-2>"
if [[ "$STATUS" == *" "* ]]; then
  STATUS="\"$STATUS\""
fi

# Build JQL query using validated variables
JQL_QUERY="project = $PROJECT AND status = $STATUS ORDER BY updated DESC"

# Execute search with validated JQL query
acli jira workitem search \
  --jql "$JQL_QUERY" \
  --fields key,summary,status,assignee,updated,priority \
  --limit 50 \
  --json
```

**Note:** The example above shows validation for a simple project + status query. Adapt the validation pattern based on the actual JQL template used (see Step 2 templates). Always validate inputs against expected patterns before building JQL.

**Field Options:**
- `key`: Issue key (always include)
- `summary`: Issue title (always include)
- `status`: Current status (always include)
- `assignee`: Assignee name (recommended)
- `updated`: Last update date (recommended)
- `priority`: Priority level (optional)
- `created`: Creation date (optional)
- `duedate`: Due date (optional)
- `labels`: Labels (optional)
- `components`: Components (optional)

**Pagination:**
- Use `--limit N` to control number of results (default: 50, max: 100)
- Use `--paginate` to fetch all results across multiple pages

### Step 4: Parse and Format Results

Parse the JSON output and format as a table:

```
Found 15 tickets matching: project = AIPCC AND status = "In Progress"

KEY          STATUS        ASSIGNEE      UPDATED     SUMMARY
─────────────────────────────────────────────────────────────────────
AIPCC-1234   In Progress   code-samurai      2024-03-20  Fix duplicate CI runs
AIPCC-5678   In Progress   super-picky-reviewer    2024-03-19  Add wheel signing support
AIPCC-910    In Progress   Unassigned    2024-03-18  Update documentation
...
```

For smaller result sets (< 10 tickets), show more detail:

```
=== 3 tickets found ===

1. AIPCC-1234: Fix duplicate CI pipeline runs
   Status: In Progress → Code Review
   Assignee: code-samurai
   Priority: High
   Updated: 2024-03-20
   https://redhat.atlassian.net/browse/AIPCC-1234

2. AIPCC-5678: Add wheel signing support
   Status: In Progress
   Assignee: super-picky-reviewer
   Priority: Medium
   Updated: 2024-03-19
   https://redhat.atlassian.net/browse/AIPCC-5678

3. AIPCC-910: Update documentation for new API
   Status: In Progress
   Assignee: Unassigned
   Priority: Low
   Updated: 2024-03-18
   https://redhat.atlassian.net/browse/AIPCC-910
```

### Step 5: Offer Export Options

After displaying results, offer to:

1. **Export to CSV**: Save results to a file for spreadsheet analysis
2. **View specific ticket**: Jump to detailed view using `jira-workitem-view` skill
3. **Refine search**: Modify the JQL query to narrow or broaden results

**CSV Export:**
```bash
# Use the same validated JQL_QUERY from Step 3
TEMP_CSV=$(mktemp -t jira-search-results.XXXXXX.csv)
acli jira workitem search \
  --jql "$JQL_QUERY" \
  --fields key,summary,status,assignee,updated,priority \
  --csv > "$TEMP_CSV"
echo "Results exported to: $TEMP_CSV"
```

### Step 6: Store Ticket Keys for Bulk Operations

Extract the list of ticket keys from results and store them for potential bulk operations:

```
Ticket keys: AIPCC-1234, AIPCC-5678, AIPCC-910

Use these keys with other skills for bulk operations.
```

## Advanced Features

### Combining Multiple Criteria

```jql
project = AIPCC
  AND status IN ("To Do", "In Progress")
  AND assignee = currentUser()
  AND priority IN (High, Highest)
  ORDER BY priority DESC, updated DESC
```

### Using Functions

- `currentUser()`: Current authenticated user
- `now()`: Current date/time
- `startOfWeek()`, `endOfWeek()`: Week boundaries
- `startOfMonth()`, `endOfMonth()`: Month boundaries

### Text Search

```jql
project = AIPCC AND text ~ "wheel building" ORDER BY updated DESC
```

### Custom Fields

For AIPCC-specific fields:

```jql
project = AIPCC AND "Color Status" = Red ORDER BY updated DESC
```

## Error Handling

- **acli not found**: Delegate to `acli-setup-check` skill
- **Authentication failure**: Delegate to `acli-setup-check` skill
- **Invalid JQL syntax**: Display error and suggest correcting the query
- **No results found**: Inform user and suggest broadening the search
- **Permission denied**: User may not have access to queried projects
- **Field not found**: Verify field name exists in the project schema

## Examples

### My Open Tickets

```text
User: /jira-workitem-search Show my open tickets
Assistant: [Searches with: assignee = currentUser() AND resolution = Unresolved]
Found 5 open tickets assigned to you:
[Displays results in table format]
```

### Project Backlog

```text
User: What's in the AIPCC backlog?
Assistant: [Searches with: project = AIPCC AND status != Done]
Found 47 tickets in the AIPCC backlog
[Displays results with pagination]
```

### Recent Activity

```text
User: What tickets were updated in the last week?
Assistant: [Searches with: updatedDate >= -7d]
Found 23 tickets updated in the last 7 days
[Displays results ordered by update time]
```

### Export to CSV

```text
User: Export all AIPCC bugs to CSV
Assistant: [Searches and exports]
Exported 156 tickets to /tmp/jira-search-results.csv
```

### Refine Search

```text
User: /jira-workitem-search project = AIPCC AND status = "In Progress"
Assistant: [Shows 15 results]
User: Only show high priority ones
Assistant: [Refines to: project = AIPCC AND status = "In Progress" AND priority = High]
Found 3 high-priority tickets in progress
[Displays refined results]
```
