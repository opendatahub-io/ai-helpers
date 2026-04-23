---
name: acli-setup-check
description: Verify acli installation and authentication. Checks if acli is installed, properly configured, and can access Jira. Use when troubleshooting acli issues or setting up acli for the first time.
allowed-tools: Bash
user-invocable: true
---

# ACLi Setup Check

Verify that the `acli` CLI tool is installed, authenticated, and can access Jira.

## Implementation

### Step 1: Check if acli is Installed

Run the following command to check if `acli` is available:

```bash
which acli
```

If the command returns a path (e.g., `/usr/local/bin/acli`), proceed to Step 2.

If the command returns nothing or "not found":

1. Inform the user that acli is not installed
2. Provide installation instructions:
   ```text
   acli is not installed. Please install it from:
   https://developer.atlassian.com/cloud/acli/guides/install-acli/

   After installation, run:
     acli jira auth
   ```
3. Stop execution

### Step 2: Test Authentication

Test if acli is authenticated by checking the authentication status:

```bash
acli jira auth status 2>&1
```

This command checks if acli is properly authenticated without
requiring access to specific projects.

Analyze the output:

- **Success**: If the command shows "✓ Authenticated" along with site and email details, authentication is working. Proceed to Step 3.
- **Authentication Error**: If the output indicates no authentication or invalid credentials:
  1. Inform the user that authentication has failed
  2. Guide them to run:
     ```text
     acli jira auth
     ```
  3. Explain they'll need their Jira API token from https://id.atlassian.com/manage-profile/security/api-tokens
  4. Stop execution

### Step 3: Report Success

If authentication is successful, report success to the user:

```text
✓ acli is installed and authenticated
✓ Connected to: https://redhat.atlassian.net

You're ready to use acli-based Jira skills!
```

## Error Handling

- **acli not found**: Provide installation instructions and stop
- **Authentication failure**: Guide user to run `acli jira auth` and stop
- **Network errors**: Report the error and suggest checking network connectivity
- **Permission denied**: Inform user they may not have access to the queried projects

## Examples

### Successful Setup Check

```text
User: /acli-setup-check
Assistant:
✓ acli is installed at /usr/local/bin/acli
✓ Connected to: https://redhat.atlassian.net

You're ready to use acli-based Jira skills!
```
