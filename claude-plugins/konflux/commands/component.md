---
argument-hint: <subcommand> [args]
description: Manage Konflux component
---

## Name
konflux:component

## Synopsis

```
/konflux:component status <component>
/konflux:component build <components> [--wait duration] [--nudge] [--wait-for-release release-duration]
```

## Description
The `konflux:component` command to manage Konflux component(s).

This command helps you:
- Get status of a component - last build, commit message, snapshot and release
- Trigger build of a component and wait until the build or release is done

## Implementation

### Subcommand: status

The command performs the following steps:

1. **Prerequisites Check**:
    - Verify `oc` CLI is installed: `which oc`
    - Verify cluster access: `oc whoami`
    - If not installed or not authenticated, provide clear instructions
    - Verify `git` CLI is installed: `which git`
    - Verify the current directory is a Git repository: `git remote -v`

2. **Parse Arguments**:
    - `component`: Component name (required)

3. **List components**:
    - Get component
      ```bash
      kubeclt get component {component} -o yaml
      ```
    - The application name is provided `.spec.application`
    - The component name is provided `.spec.componentName`
    - The Git repository URL is provided `.spec.source.git.url`
    - The commit SHA is provided `.status.lastBuiltCommit`
    - The image is provided `.status.lastPromotedImage`

4. **Get Git information**:
    - Use `git branch -a --contains <commit-sha>` to find the branch name
    - The Git repository should be in the current working directory. If it is not fail the command.

5. **Get Snapshots**:
    - Get snapshots of the component and order by oldest
      ```bash
      kubectl get snapshot -l pac.test.appstudio.openshift.io/sha={commit},appstudio.openshift.io/component={component} --sort-by=.metadata.creationTimestamp
      ```

6. **Get Releases**:
    - Get releases object for each snapshot
      ```bash
      kubectl get release -l pac.test.appstudio.openshift.io/sha={commit},appstudio.openshift.io/component={component}
      ```
   - The snapshot is specified in `.spec.snapshot`
   - The `.status.conditions` show if the release failed or succeeded

7. **Display result**:
   - Display the result:
     ```
     | Component        | Built SHA | lastPromotedImage    |  Commit Message             | Git Branch   | Snapshots (oldest first) |
     |------------------|-----------|----------------------|-----------------------------|--------------|--------------------------|
     | {component}      | {commit}  | {lastPromotedImage}  | {commit-message}            | {git-branch} | {snapshots}              |
     | otel-bundle-main | 8ba2e60   |                      | Fix service account (#693)  | main         | otel-main-jnhfz          |
     ```
   - Display snapshot with release information for each snapshot
     ```
     Component: {component}
     | Snapshot        | Release                       | Release status                           |
     |-----------------|-------------------------------|------------------------------------------|
     | {snapshot}      | {release}                     | {release-status}                         |
     | otel-main-jnhfz | otel-main-jnhfz-8ba2e60-nnwnp | Failed (ManagedPipelineProcessed failed) |
     ```

### Subcommand: build

The command performs the following steps:

1. **Prerequisites Check**:
    - Verify `oc` CLI is installed: `which oc`
    - Verify cluster access: `oc whoami`
    - If not installed or not authenticated, provide clear instructions
    - Verify `git` CLI is installed: `which git`
    - Verify the current directory is a Git repository

2. **Parse Arguments**:
    - `$1`: Component(s) (required): Konflux Component(s) name
    - `$2`: flag `--wait <duration>` (optional) wait duration for the build to finish
      - The duration can have suffix `s` for seconds, `m` for minutes or `h` for hours.
      - If other suffixes are specified fail the command
    - `$3`: flag `--nudge` (optional) nudge files after the build finishes
      - `--nudge` can be used only if `--wait` is used
    - `$4`: flag `--wait-for-release <release-duration>` (optional) wait until release is done
       - `--wait-for-release` can be used only if `--wait` is used
       - The duration can have suffix `s` for seconds, `m` for minutes or `h` for hours.

3. **Trigger the build**:
    - Annotate each component to trigger the build
      ```bash
      kubectl annotate components/{compponent} build.appstudio.openshift.io/request=trigger-pac-build
      ```

4. **Get the build information**:
      ```bash
      kubectl get pipelinerun -l appstudio.openshift.io/component={component}
      ```
    - Wait up to 5 minutes, it takes time for the PipelineRun to be created
    - The started pipeline name must have `-on-push` in the name

5. **Wait for the build to finish**:
   - If `--wait <duration>` is provided wait for the PipelineRun to finish. The duration can be in `s` for seconds, `m` for minutes or `h` for hours.
   ```bash
   kubectl wait --for=condition=Suceeded=true pipelinerun/{pipelinerun} --timeout={duration}
   ```
   - Extract the nudge files specified in the `.metadata.annotations["build.appstudio.openshift.io/build-nudge-files"]` in the PipelineRun
   - The Snapshot object is created when the build finishes
   - Get the Snapshot object and extract container image `.spec.components[?(@.name=="{component}")].containerImage`
     ```bash
     kubectl get snapshot -l appstudio.openshift.io/build-pipelinerun={pipelinerun}
     ```
   - If the build fails use the troubleshooting instructions to explain the failure

6. **Wait for the release to finish**:
    - If `--wait-for-release <release-duration>` is provided wait for the Release to finish. The release-duration can be in `s` for seconds, `m` for minutes or `h` for hours.
   ```bash
   kubectl wait --for=condition=Released=true --timeout={release-duration} -l appstudio.openshift.io/build-pipelinerun={pipelinerun}
   ```

7. **Nudge files**:
    - If `--wait <duration>` and `--nudge` are provided nudge the files by repacing the `containerImage` in those files

8. **Display result**:
    - Display the result:
      ```
      Component: {component} | PipelineRun: {pipelinerun-name} | Snapshot: {snapshot} | Container Image: {containerImage}
      ```

## Return Value
- **status**: Table of all components
- **build**: PipelineRun custom resource name which is executing the build and snapshot if the build finished

## Examples

1. **Get status of otel-collector-main component**:
   ```bash
   /konflux:component status otel-collector-main
   ```

2. **Trigger build of the otel-collector-main component**:
   ```bash
   /konflux:component build otel-collector-main
   ```

3. **Trigger build of the otel-collector-main and otel-operator-main component**:
   ```bash
   /konflux:component build otel-collector-main otel-operator-main
   ```

4. **Trigger build of the otel-collector-main component and wait 30 minutes to finish**:
   ```bash
   /konflux:component build otel-collector-main --wait 30m
   ```
## Arguments

### status

- **component** (required): Name of the Konflux component

### build

- **component** (required): Name of the Konflux component
- **--wait <duration>** (required): Duration how long to wait for the pipelinerun to finish

## Troubleshooting

### build

- ***PipelineRun progress and failure***:
    - The PipelineRun creates TaskRun(s) objects which create actuall pods to run the build.
    - The TaskRun for a specific PipelineRun can be found by `kubectl get taskrun -l tekton.dev/pipelineRun={pipelinerun}`
    - The pod for a specific TaskRun can be found by `kubectl get pod -l tekton.dev/taskRun={taskrun}`
    - Get the pod logs, kubernetes events, status and explain the failure

- ***Release progress and failure***
    - The release is executed as a PipelineRun. The release PipelineRun is defined in the Release object in `.status.managedProcessing.pipelineRun`
    - The example value is `rhtap-releng-tenant/managed-vks2b`. Which means the PipelineRun name is `managed-vks2b` and runs in `rhtap-releng-tenant` Kubernetes namespace.
    - The TaskRun for the release PipelineRun can be found by `kubectl get taskrun -l tekton.dev/pipelineRun={pipelinerun} -n {namespace}`
    - The pod for the release TaskRun can be found by `kubectl get pod -l tekton.dev/taskRun={taskrun} -n {namespace}`

## Related Commands

* `/konflux:application status <application>` - Show application status

## Additional Resources

- [Konflux upstream documentation](https://konflux-ci.dev/docs/)
- [Konflux architecture documentation](https://github.com/konflux-ci/architecture)
