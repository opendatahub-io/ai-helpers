---
name: jira-aipcc-create
description: Create Jira issues in the AIPCC project. Infers summary, description, type, and component from conversation context, confirms with the user before creating. Use when the user wants to file a new AIPCC Jira issue.
allowed-tools: Bash, AskUserQuestion
user-invocable: true
---

# Create AIPCC Jira Issue

Create Jira issues in the AIPCC project using the `acli` CLI.

## Prerequisites

- `acli` must be installed and authenticated (`acli jira auth`)

## Implementation

### Step 1: Infer Issue Details from Context

Analyze the conversation to determine:

1. **Summary**: A concise title (under 100 characters) describing the issue
2. **Description**: A Markdown description with relevant context, root cause, fix details, or requirements (use Markdown)
3. **Type**: One of the following based on the nature of work
   - `Bug`: problem that impairs or prevents product functions; tracks escaped defects
   - `Story`: action-oriented, smallest unit of work that can be completed within one sprint
   - `Epic`: large user story that needs to be broken down; groups bugs, stories, and tasks to show progress of a larger effort; represents significant deliverable; does not span teams
   - `Feature`: use when tracking capability or well-defined set of functionality delivering business value; can include additions/changes to existing functionality
   - `Spike`: time-bound unit of work representing research-related task; not easy to size
   - `Initiative`: use when capturing internal improvements
   - `Task`: unit of work to be accomplished, not end-user facing
4. **Component**: One of the valid AIPCC components:
   - `PyTorch`
   - `AIPCC Productization`
   - `Accelerator Enablement`
   - `Wheel Package Index`
   - `AI Testing + Workflow Validation`
   - `Model Validation`
   - `Development Platform`

If any field cannot be confidently inferred, ask the user.

### Step 2: Confirm with the User

Present the proposed issue details to the user in a clear format:

```
I'll create the following AIPCC JIRA issue:

**Type**: Bug
**Component**: Wheel Package Index
**Summary**: Fix duplicate CI pipeline runs
**Description**:
> [description]

Shall I go ahead and create this?
```

Wait for user confirmation before proceeding. If the user requests changes, adjust accordingly.

### Step 3: Create the Issue

Build a JSON file with the following structure:

```json
{
  "projectKey": "AIPCC",
  "summary": "<summary>",
  "type": "<type>",
  "description": "<description in plain text>",
  "additionalAttributes": {
    "components": [{"name": "<component>"}]
  }
}
```

Write it to a temporary file:

```bash
cat > "$(mktemp /tmp/acli-issue-create-XXXX.json)" << 'EOF'
{ ... }
EOF
```

Create the issue using:

```bash
acli jira workitem create --from-json <JSON-FILE>
```

### Step 4: Report Result

On success, `acli` prints the new issue key and URL. Report this to the user:

```
Created AIPCC-12345: https://redhat.atlassian.net/browse/AIPCC-12345
```

Clean up the temporary JSON file after creation.

## Error Handling

- **acli not found**: Tell the user to install acli and run `acli jira auth`
- **Authentication failure**: Tell the user to run `acli jira auth`
- **Creation failure**: Display the error from acli and suggest checking permissions
- **Invalid component**: Show the list of valid components and ask the user to pick one

## Examples

### Context-Aware Creation

```text
User: [After discussing a bug fix] Create a JIRA for this
Assistant: [Infers details from conversation, presents for confirmation, creates on approval]
```

### Explicit Request

```text
User: /jira.aipcc-create Bug: selfservice build monitoring flakes
Assistant: [Uses provided info, infers description and component, confirms, creates]
```

### Ambiguous Component

```text
User: File a task for updating the CI pipeline docs
Assistant: I'll create an AIPCC task. Which component does this fall under?
  1. AIPCC Productization
  2. Wheel Package Index
  3. Development Platform
  ...
```
