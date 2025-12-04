# Konflux Plugin

A comprehensive plugin for triggering Konflux builds and analyzing state of the Konflux Application.

## Overview

This plugin provides these Konflux capabilities:

- **Component Management**: Search Konflux components, trigger builds, wait for release and nudge files
- **Application Management**: Search and understand status of Konflux application and all its components

### Example build and release

This commands in this plugin can be used to build and release a product on Konflux. With the following workflow
a developer has all builds under control, AI agent can understand the TaskRun failures nudging is explicit (it does not rely on MintMaker).

First build components:
```bash
/konflux:component build otel-collector-main otel-target-allocator-main otel-operator-main --wait 1h --nudge
```
The command executes builds of these 3 components and instructs AI agent to nudge the dependent files (in this case the OLM bundle).

Then a developer commits the changes and pushes them to the repository.
Once the changes are merged the bundle can be built:

```bash
/konflux:component build otel-bundle-main --wait 1h --wait-release 1h --nudge
```
The command instructs Konflux to build the bundle, nudge dependent files and wait for the release.
In this case the nudge changes the FBC catalog template.

## Prerequisites

- Claude Code installed
- OpenShift CLI (`oc`) installed and configured
- Access to an OpenShift cluster with Konflux
- The current working directory is a Konflux git project with Tekton pipelines (`./tekton`)

## Commands

### `/konflux:component` - Get status of Konflux component, trigger builds and wait for release to finish

**Usage:**
```bash
/konflux:component status sotel-collector-main                                 # Get status of a component
/konflux:component build otel-collector-main otel-collector-main               # Trigger build of 2 components
/konflux:component build otel-collector-main --wait 1h                         # Trigger build of a component and wait for the build to finish
/konflux:component build otel-collector-main --wait 1h --nudge                 # Trigger build of a component, wait for the build to finish and nudge dependent files (e.g. OLM bundle)
/konflux:component build otel-bundle-main --wait 1h --nudge --wait-for-release # Trigger build of a component, wait for the build and release to finish and nudge files (e.g. FBC catalog template)
```

**What it does:**
- Gets status of a component: last build, Snapshots, Git SHA with message
- Builds components, waits for the build and/or release to finish
- Nudges dependent files are build

**Arguments:**
- `component(s)` (required): List of components
- `--wait <duration>` (optional): Wait for the build to finish
- `--nudge` (optional): Nudge dependent files are build
- `--wait-for-release <duration>` (optional): Wait for the release to finish

See [commands/component](commands/component.md) for full documentation.

---

### `/konflux:application` - Get status of Konflux application

**Usage:**
```bash
/konflux:application status otel-main        # Get status of Application - e.g. all its components with recent Releases
```

**What it does:**
- Gets status of an application: its components, last snapshots, builds and releases

**Arguments:**
- `application` (required): Application name

See [commands/application.md](commands/application.md) for full documentation.

---

## Resources

- [Konflux upstream Documentation](https://konflux-ci.dev/docs/)
- [Konflux Red Hat Documentation](https://konflux.pages.redhat.com/docs/users/index.html)
- [Konflux Architecture](https://github.com/konflux-ci/architecture)
- [Konflux Claude Code Skills](https://github.com/konflux-ci/skills)
