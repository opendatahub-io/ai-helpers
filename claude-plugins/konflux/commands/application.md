---
argument-hint: <subcommand> [args]
description: Manage Konflux application
---

## Name
konflux:application

## Synopsis

```
/konflux:application status <application>
```

## Description
The `konflux:application` command to manage Konflux application.

This command helps you:
- List all components in the application
- Understand the status of the components in the application - last build, snapshots, releases

## Implementation

### Subcommand: status

The command performs the following steps:

1. **Prerequisites Check**:
    - Verify `oc` CLI is installed: `which oc`
    - Verify cluster access: `oc whoami`
    - If not installed or not authenticated, provide clear instructions
    - Verify `jq` CLI is installed: `which jq`
    - Verify `git` CLI is installed: `which git`
    - Verify the current directory is a Git repository: `git remote -v`

2. **Parse Arguments**:
    - `application`: Application name (required)

3. **List components that belong to the application**:
    - Get components
      ```bash
      kubeclt get component -o yaml | jq '.items[] | select(.spec.application=="{application}")
      ```
    - The application name is provided in `.spec.application`
    - The component name is provided in `.spec.componentName`
    - The Git repository URL is provided in `.spec.source.git.url`
    - The commit SHA is provided in `.status.lastBuiltCommit`

4. **Show status for each Konflux component**:
    - Run the following Claude Code command to get status of each Konflux component from the application
    ```bash
    /konflux:component status {component}
    ```


## Return Value
- **status**: Table of all components that belong to the provided application

## Examples

1. **Get status all components of the otel-main application**:
   ```bash
   /konflux:application status otel-main
   ```

## Arguments

### status

- **application** (required): Name of the Konflux application

## Troubleshooting


## Related Commands

* `/konflux:component status <component>` - Show component status
* `/konflux:component build <components> [--wait <duration>] [--wait-release <duration>] [--nudge]` - Trigger component build

## Additional Resources

- [Konflux upstream documentation](https://konflux-ci.dev/docs/)
- [Konflux architecture documentation](https://github.com/konflux-ci/architecture)
