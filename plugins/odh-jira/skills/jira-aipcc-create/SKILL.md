---
name: jira-aipcc-create
description: Create AIPCC-org Jira issues in the RHAI project. Infers summary, description, type, and component from conversation context, confirms with the user before creating. Use when the user wants to file a new AIPCC Jira issue.
allowed-tools: Bash, AskUserQuestion
user-invocable: true
---

# Create AIPCC Jira Issue

Create Jira issues for the AIPCC org in the RHAI project using the `acli` CLI. Every issue is created with the `Red Hat Employee` security level, so only Red Hat employees can see it.

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
   - `Accelerator Enablement`
   - `AI Testing + Workflow Validation`
   - `AIPCC Ecosystems`
   - `AIPCC Productization`
   - `Model Validation`
   - `PyTorch`
   - `Wheel Building`
   - `Wheel Package Index`

5. **Parent Epic** (optional): If the user specifies an epic key (e.g. RHAI-1234), include it as the parent

If any field cannot be confidently inferred, ask the user.

### Step 2: Confirm with the User

Present the proposed issue details to the user in a clear format:

```text
I'll create the following AIPCC JIRA issue:

**Type**: Bug
**Component**: Wheel Package Index
**Parent Epic**: RHAI-1234 (if specified)
**Visibility**: Red Hat Employee
**Summary**: Fix duplicate CI pipeline runs
**Description**:
> [description]

Shall I go ahead and create this?
```

Wait for user confirmation before proceeding. If the user requests changes, adjust accordingly.

### Step 3: Create the Issue

Build a JSON file with the following structure.

**Important**: The `description` field MUST be in Atlassian Document Format (ADF), not plain text. `acli` will reject plain text descriptions with an error.

If the user specifies a parent epic, include the `parent` field in `additionalAttributes`. This is the only way to set the epic/parent relationship — `acli jira workitem edit` does not support `additionalAttributes` or custom fields, so the parent must be set at creation time.

Always include the `security` field in `additionalAttributes`, exactly as shown: `10034` is the `Red Hat Employee` security level in RHAI. Never omit or change it. Like the parent, it can't be set afterwards with `acli jira workitem edit`.

```json
{
  "projectKey": "RHAI",
  "summary": "<summary>",
  "type": "<type>",
  "description": {
    "version": 1,
    "type": "doc",
    "content": [
      {
        "type": "paragraph",
        "content": [
          {
            "type": "text",
            "text": "<description text>"
          }
        ]
      }
    ]
  },
  "additionalAttributes": {
    "security": {"id": "10034"},
    "components": [{"name": "<component>"}],
    "parent": {"key": "<EPIC-KEY>"}
  }
}
```

Omit the `parent` field from `additionalAttributes` if no epic is specified. Keep `security` in every case.

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

On success, `acli` prints the new issue key and URL. Before reporting, read the security level back:

```bash
acli jira workitem view <ISSUE-KEY> --fields security --json
```

`fields.security` in the output must have the `id` `10034` and the `name` `Red Hat Employee`. If it does, report this to the user:

```text
Created RHAI-12345: https://redhat.atlassian.net/browse/RHAI-12345
Visibility: Red Hat Employee
```

If the security level is missing or different, don't report success. Tell the user right away that the issue exists without the expected visibility, with its key and URL, so they can set the security level in Jira by hand (`acli` can't edit it).

If the `acli jira workitem view` command itself fails, the issue still exists: never create it again. Retry only that command. If it keeps failing, report the key and URL and say that the visibility is unverified, so the user can check it in Jira.

Clean up the temporary JSON file after creation.

## Error Handling

- **acli not found**: Tell the user to install acli and run `acli jira auth`
- **Authentication failure**: Tell the user to run `acli jira auth`
- **Creation failure**: Display the error from acli and suggest checking permissions
- **Security level missing or wrong after creation**: Don't report success. Give the user the issue key and URL and ask them to set the security level to `Red Hat Employee` in Jira
- **Security level read-back fails**: Don't run the creation again. Retry the `acli jira workitem view` command, and if it still fails, report the issue key and URL with the visibility marked as unverified
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
  3. Wheel Building
  ...
```
