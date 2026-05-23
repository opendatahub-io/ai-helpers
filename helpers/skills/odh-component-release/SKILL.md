---
name: odh-component-release
description: >-
  Drive the per-component ODH code-freeze release for an llm-d component:
  create the release branch on the opendatahub-io repo, trigger the Konflux
  release onboarder workflow for each Konflux sub-component, then verify
  the onboarder PR and the resulting Quay image. Use when asked to cut an
  ODH release for a component, run ODH release steps for one component,
  or prepare a component for ODH code freeze.
argument-hint: "<component> --version <vX.Y.Z> [--dry-run] [--from-step N] [--wait-quay <seconds>]"
allowed-tools: Bash Read AskUserQuestion
user-invocable: true
compatibility: Requires gh (authenticated to opendatahub-io), yq, jq, skopeo.
metadata:
  author: opendatahub-io
  version: "1.0"
  tags: odh, release, konflux, quay, llm-d
---

# ODH Per-Component Release

Automates the four manual steps a component-team engineer performs during
ODH code-freeze Friday for one llm-d-derived component:

1. Create the `release-vX.Y.Z` branch on the opendatahub-io component repo
2. Trigger `odh-konflux-release-onboarder.yml` (once per Konflux sub-component)
3. Verify the onboarder opened its PR against the release branch
4. Verify each Quay image tag was produced

Source: `llm-d-inference-engineering-docs/content/release-engineering/onboarding-component.md`,
section "ODH Release Process(new images)".

A user **checkpoint** runs before every side-effecting step (branch creation
and workflow trigger). `--dry-run` reports what would happen and skips all
side effects. `--from-step N` resumes from step N (1–4) and skips earlier
steps — useful when re-running after a failure.

## Step 0: Parse arguments and load config

Parse `$ARGUMENTS`:

- **component** (positional, required): the short name from the registry
- **--version vX.Y.Z** (required): the release tag (validate with
  pattern `^v[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.]+)?$`)
- **--dry-run** (optional): no side effects
- **--from-step N** (optional, default `1`): skip steps before N
- **--wait-quay <seconds>** (optional, default `0`): in step 4, poll Quay for
  up to this many seconds waiting for the tag to appear

If `component` or `--version` is missing, list valid component names from
the config and prompt via `AskUserQuestion`.

Resolve the skill directory and load the config:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-$(cd "$(dirname "$0")" && pwd)}"
CONFIG="${SKILL_DIR}/references/components.yaml"

KONFLUX_CENTRAL=$(yq -r '.release.konflux_central_repo' "${CONFIG}")
ONBOARDER_WORKFLOW=$(yq -r '.release.onboarder_workflow' "${CONFIG}")
KONFLUX_APP_URL=$(yq -r '.release.konflux_release_app_url' "${CONFIG}")
QUAY_ORG=$(yq -r '.release.quay_org' "${CONFIG}")
BRANCH_PREFIX=$(yq -r '.release.release_branch_prefix' "${CONFIG}")

ODH_REPO=$(yq -r ".components.\"${COMPONENT}\".odh_repo" "${CONFIG}")
ODH_DEFAULT_BRANCH=$(yq -r ".components.\"${COMPONENT}\".odh_default_branch" "${CONFIG}")
```

If `ODH_REPO` is `null`, the component is not in the registry. List the
keys under `.components` from the config and stop.

Compute the release branch name:

```bash
RELEASE_BRANCH="${BRANCH_PREFIX}${VERSION}"
```

Run preflight:

```bash
bash "${SKILL_DIR}/scripts/preflight.sh"
```

If preflight fails, stop.

Print a one-screen summary of what will happen, then continue to step 1
(or `--from-step` if set):

```text
Component:        <component>
ODH repo:         <org/repo>
Release branch:   release-vX.Y.Z (from <default-branch>)
Konflux central:  <central repo>
Konflux sub-components: <list>
Quay org:         opendatahub
Mode:             normal | dry-run
Starting step:    1 | N
```

## Step 1: Create the release branch

Read the current branches once so the user sees the actual state before the
checkpoint:

```bash
bash "${SKILL_DIR}/scripts/create-release-branch.sh" \
    --repo "${ODH_REPO}" \
    --branch "${RELEASE_BRANCH}" \
    --base-branch "${ODH_DEFAULT_BRANCH}" \
    --dry-run
```

Parse `status=` from the output:

- `exists` → tell the user the branch is already there; skip to step 2.
- `would-create` → continue with the checkpoint below.

**Checkpoint** (`AskUserQuestion`):

> Create branch `release-vX.Y.Z` on `<ODH_REPO>` from `<default-branch>`
> (SHA `<short-sha>`)? This is visible on the GitHub repository.

If the user declines, stop. If `--dry-run` is set, report and skip.

Otherwise re-run the script without `--dry-run`. Report the resulting
status, short SHA, and tree URL.

## Step 2: Trigger the Konflux release onboarder

Read the Konflux sub-components from the config:

```bash
mapfile -t KONFLUX_COMPONENTS < <(
    yq -r ".components.\"${COMPONENT}\".konflux_components[].name" "${CONFIG}"
)
```

Build a table of the exact inputs each invocation will send. Use these
values verbatim — they mirror the manual UI form documented in
`onboarding-component.md`:

| Input             | Value                       |
|-------------------|-----------------------------|
| repository_name   | `<konflux-sub-component>`   |
| branch            | `release-vX.Y.Z`            |
| image_branch      | `release-vX.Y.Z`            |
| release_type      | `Release`                   |
| version           | `vX.Y.Z`                    |

**Checkpoint** (`AskUserQuestion`):

> Trigger `odh-konflux-release-onboarder.yml` on `<KONFLUX_CENTRAL>` for
> N Konflux sub-component(s): <comma-list>? Each run opens a PR on
> `<ODH_REPO>` and configures Konflux to build the image.

If the user declines, stop. If `--dry-run`, report each invocation and skip.

For each entry in `KONFLUX_COMPONENTS`:

```bash
bash "${SKILL_DIR}/scripts/trigger-onboarder.sh" \
    --konflux-central "${KONFLUX_CENTRAL}" \
    --workflow "${ONBOARDER_WORKFLOW}" \
    --component "${konflux_component}" \
    --release-branch "${RELEASE_BRANCH}" \
    --version "${VERSION}"
```

If a run fails with input-validation errors, the workflow's accepted inputs
may have changed. Inspect them and adjust:

```bash
gh workflow view "${ONBOARDER_WORKFLOW}" --repo "${KONFLUX_CENTRAL}" --yaml \
    | head -60
```

Report the `run_url` for each invocation so the user can follow it. The
runs are async; later steps verify their effect rather than waiting here.

## Step 3: Verify the onboarder PR

For each Konflux sub-component, look for the PR the onboarder opens on the
component repo against the release branch:

```bash
bash "${SKILL_DIR}/scripts/verify-konflux-pr.sh" \
    --component-repo "${ODH_REPO}" \
    --release-branch "${RELEASE_BRANCH}" \
    --konflux-component "${konflux_component}"
```

For each result:

- `status=found` → report the PR number, state (OPEN/MERGED/CLOSED), and URL.
- `status=missing` → tell the user the onboarder PR has not appeared yet
  (the workflow may still be running), and suggest checking the run URL
  from step 2.

Also surface the Konflux UI link so the user can confirm the component
exists in the release application:

```text
Konflux UI: <KONFLUX_APP_URL>/components/<konflux-sub-component>
```

If any onboarder PR is missing, do not fail the skill — the workflow can
take several minutes. Tell the user to re-run with `--from-step 3` once
the workflow runs from step 2 have completed.

## Step 4: Verify the Quay image tag

For each Konflux sub-component, resolve its `quay_image` from the config
and check for the tag:

```bash
quay_image=$(yq -r \
    ".components.\"${COMPONENT}\".konflux_components[]
      | select(.name == \"${konflux_component}\")
      | .quay_image" "${CONFIG}")

bash "${SKILL_DIR}/scripts/verify-quay-image.sh" \
    --org "${QUAY_ORG}" \
    --image "${quay_image}" \
    --tag "${VERSION}" \
    --wait-seconds "${WAIT_QUAY:-0}"
```

For each result:

- `status=found` → report `ref` and `digest`.
- `status=missing` → report the browse URL and note that builds are
  triggered per commit on the release branch; the tag normally appears
  within a few minutes of the onboarder PR being merged.

## Final report

Print a compact table summarizing every sub-component:

```text
Component:  <component>   Version: vX.Y.Z   Branch: release-vX.Y.Z

  release-branch:        <created|exists|would-create>  <short-sha>
  <konflux-sub-1>
    onboarder run:       <run_url>
    onboarder PR:        <pr_state> <pr_url>
    quay image:          <found|missing>  quay.io/opendatahub/<image>:vX.Y.Z
  <konflux-sub-2>
    ...
```

Then state which next manual action (if any) is needed: usually
"merge the onboarder PR(s), then re-run with `--from-step 4 --wait-quay 600`
to wait for the image tag(s)".

## Gotchas

- **Step 2 is asynchronous.** `gh workflow run` returns immediately; the
  actual onboarder run takes several minutes. Do not interpret a missing
  PR in step 3 as a failure on the first pass — re-run with `--from-step 3`
  later.
- **One ODH repo can produce multiple Konflux components.** Always iterate
  over `konflux_components` from the registry; never assume one repo = one
  image. `inference-scheduler` and `batch-gateway` each produce two images
  from a single repo.
- **`konflux_component.name` must match the workflow dropdown exactly.**
  The onboarder validates `repository_name` against a fixed list. If
  triggering fails with an input-validation error, inspect the workflow
  with `gh workflow view <workflow> --repo <central> --yaml` and fix the
  `name` in `references/components.yaml`.
- **The release-branch name is derived, not configurable per component.**
  All components use `release-<version>` (e.g. `release-v0.5.1`) by default.
  If a component team needs a different prefix, update
  `release.release_branch_prefix` in the config rather than special-casing
  the script.
- **Quay tags appear only after the onboarder PR is merged and the resulting
  Konflux PipelineRun completes.** Step 4 with `--wait-quay 0` will almost
  always report `missing` if run immediately after step 2 — that is
  expected. Use `--wait-quay 600` after merging the onboarder PR(s).
- **The skill never merges the onboarder PR.** Merging is left to the
  component team's normal review process. The skill only opens visibility
  into where the PR is and whether the image landed.
- **Authentication scope.** `gh` must be authenticated against an account
  with write access to the opendatahub-io component repo (to create the
  release branch) and trigger access on `opendatahub-io/odh-konflux-central`
  (to dispatch the workflow). A read-only token will fail at step 1.
