---
name: odh-llm-d-release
description: >-
  Orchestrate the opendatahub-io release for all llm-d components in one
  cycle. Collects upstream(llm-d) versions, auto-discovers the release tracker
  issue, then spawns parallel sub-agents — one per component (release
  branch, Konflux onboarder workflow, PR validation, approve+merge, Quay image
  verify, GitHub draft release) plus one KServe metadata PR sub-agent —
  and posts the final #Release# tracker comment. Use when the release
  manager runs on/before ODH code-freeze date for the llm-d team.
argument-hint: "--version <vX.Y[.Z][-eaN|-ea.N]>"
allowed-tools: Bash Read AskUserQuestion Agent
user-invocable: true
compatibility: Requires gh (authenticated), yq, jq, curl, git.
metadata:
  author: zdtsw
  version: "1.0"
  tags: odh, release, llm-d, konflux, quay, kserve, opendatahub-io
---

# ODH llm-d Release Orchestrator

Runs once per ODH release cycle by the release manager. Drives release
branch creation, the Konflux onboarder workflow, onboarder-PR validation
and merge, Quay image verification, KServe metadata PR, and the tracker
comment — for every llm-d component in one shot.

**Single input:** `--version v3.5-ea2`. Three values derive from it:

| Use | Value |
|---|---|
| ODH release branch on each component repo | `release-v3.5-ea2` |
| Konflux onboarder `version` input + Quay image tag | `v3.5-ea2` |
| GitHub release tag on each component repo | `odh-v3.5-ea2` |

## Value flow (for `--version v3.5-ea2`)

This diagram shows where the version goes, what name it takes at each stop,
and which script flag receives it. Three derived values are colored below:
`B` = release branch, `T` = image tag (unchanged from `VERSION`),
`R` = GitHub release tag.

```text
release manager
 └─ /odh-llm-d-release --version v3.5-ea2

orchestrator (SKILL.md)
   VERSION       = v3.5-ea2
   RELEASE_BRANCH= release-v3.5-ea2     (B = release_branch_prefix + VERSION)
   IMAGE_TAG     = v3.5-ea2             (T = VERSION, unchanged)
   RELEASE_TAG   = odh-v3.5-ea2         (R = github_release_tag_prefix + VERSION)
 │
 ├── per-component sub-agent (one per component, in parallel)
 │     step 1  create-release-branch.sh    --branch B    → branch release-v3.5-ea2
 │     step 2  onboarder-trigger-gha.sh    --version T   → Konflux builds quay.io/.../<image>:v3.5-ea2
 │     step 6  release-image-checker.sh    --tag     T   → verifies quay.io/.../<image>:v3.5-ea2
 │     step 7  create-github-release.sh    --tag     R   → draft GH release tagged odh-v3.5-ea2
 │
 └── KServe metadata sub-agent
       open-kserve-metadata-pr.sh          --version VERSION  → PR title/branch use v3.5-ea2
                                           (the upstream component versions in --updates
                                            are SEPARATE — collected from the release
                                            manager via AskUserQuestion in step 1)
```

## Step 0 — Parse arguments and load config

Parse `$ARGUMENTS`:

- `--version <ver>` (required) — the ODH release version. Accepted forms:
  - **GA**: `v3.5`, `v3.5.0`
  - **Early Access**: `v3.5-ea1`, `v3.5-ea.1`, `v3.5.0-ea.1` (also `v3.5.0-ea1`)

Validate that `--version` matches `^v[0-9]+\.[0-9]+(\.[0-9]+)?(-[A-Za-z0-9.]+)?$`.
If missing or malformed, prompt the user via `AskUserQuestion` and stop on cancel.

Load the registry:

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-$(cd "$(dirname "$0")" && pwd)}"
CONFIG="${SKILL_DIR}/references/components.yaml"

VERSION="<parsed>"
RELEASE_BRANCH="$(yq -r '.release.release_branch_prefix' "${CONFIG}")${VERSION}"
IMAGE_TAG="${VERSION}"
RELEASE_TAG="$(yq -r '.release.github_release_tag_prefix' "${CONFIG}")${VERSION}"
```

Run the tools check:

```bash
bash "${SKILL_DIR}/scripts/tools-checker.sh"
```

If it fails, stop and surface what's missing.

## Step 1 — Collect upstream versions

For the KServe metadata PR, gather the upstream version for every component
and every entry in `kserve_extra_entries` (vLLM today). Use a **single**
`AskUserQuestion` call so the release manager fills them all in at once
rather than answering one prompt at a time.

Build the list of names to ask about:

```bash
# Per-component entries (kserve_entry_name) + extras (e.g. vLLM)
yq -r '.components | to_entries[] | .value.kserve_entry_name' "${CONFIG}"
yq -r '.release.kserve_extra_entries[]' "${CONFIG}"
```

Issue one `AskUserQuestion` with one question per name, prompting "Upstream
version for `<name>` (e.g. v0.7.1):". Cancel ⇒ stop.

Build `UPDATES` for the KServe sub-agent from the collected answers:

```json
[{"name": "llm-d-router", "version": "v0.7.1"}, ...]
```

## Step 2 — Auto-discover the tracker issue

```bash
bash "${SKILL_DIR}/scripts/tracker-issue-finder.sh" \
    --version "${VERSION}"
```

Parse the output. Behavior:

- **`tracker-issue-finder.sh` exited non-zero** (GitHub API/search failure):
  tell the user the search failed (show stderr), and ask whether to retry,
  to provide an issue number directly, or to skip the final comment step.
- `count == 0` — tell the user no tracker issue matches `${VERSION}`, ask
  whether to skip the final comment step or to provide an issue number.
- `count == 1` — show the single match (title + URL) and confirm.
- `count > 1` — show the matches in an `AskUserQuestion` and let the user
  pick.

Save `TRACKER_ISSUE_NUMBER` (or `""` if skipped).

## Step 3 — Spawn sub-agents in parallel

You will issue **one message containing multiple `Agent` tool calls** so they
all run in parallel. Build the prompts by reading the templates and
substituting variables.

### 3a — Per-component sub-agents

For each key in `.components` (iterate via `yq`):

- Read `references/per-component-task.md`.
- Substitute only `SKILL_DIR`, `COMPONENT_KEY`, `VERSION` (and optionally
  `QUAY_TIMEOUT`). The sub-agent reads everything else (ODH repo,
  default branch, workflow component, konflux files, Quay org, etc.)
  directly from `components.yaml`.
- Issue one `Agent` tool call with the substituted prompt and
  `subagent_type=general-purpose`. Description: `Release <COMPONENT_KEY>`.

### 3b — KServe metadata PR sub-agent

- Read `references/kserve-pr-task.md`.
- Substitute `SKILL_DIR`, `VERSION`, `UPDATES`. The sub-agent
  reads `kserve_metadata_file` and `kserve_keep_entries` from
  `components.yaml` directly (upstream repo and target branch are
  hardcoded in the script).
- Issue one `Agent` tool call.

All sub-agent calls go in the **same response message** so the harness
launches them concurrently. Each sub-agent returns a JSON payload (see the
template files for the schema).

## Step 4 — Wait for results and surface failures

When all sub-agent tool results return, parse each JSON payload.

For each sub-agent:

- Show a one-line summary: component name + verdict (`ok`, `partial`,
  `failed`) + key URLs (workflow run, PR, release, Quay images).
- If any per-component sub-agent reports `validation.status=fail`, show the
  `problems` array verbatim — the release manager will diagnose those
  manually.
- **If any `quay_images[].status` is `missing`**, surface a clear warning
  block with each missing `ref` and `browse_url`. Say explicitly that the
  release was completed *without* that image landing in the Quay-poll
  window; the release manager needs to confirm whether the Konflux build is
  still in progress or actually failed.
- If any sub-agent reports `errors`, surface them.

## Step 5 — Compose the #Release# tracker comment

If `TRACKER_ISSUE_NUMBER` was set (step 2), build the comment body. Format
per the doc:

```text
#Release#
- <component_name>|<release-branch>/<release-tag>|<release-notes-url>
- <component_name>|<release-branch>/<release-tag>|<release-notes-url>  (image pending — verify)
- ...
```

`component_name` uses the registry's `tracker_name` (the short form used by
humans in the tracker, e.g. `llm-d-router`, `wva`, `llm-d-kv-cache`) — not
the full `kserve_entry_name`.

**Image-pending marker.** A component is still included in the tracker
comment when any of its `quay_images` reports `missing` — the release
branch was created, the onboarder PR was merged, and a draft GH release
exists, so the line carries genuine value. Append the literal text
`(image pending — verify)` (with a single space before the backtick) at
the end of the line in that case, so the
release manager (and the tracker readers) can tell at a glance which
components need a manual Quay check.

Write the body to a temp file. Show it to the user via `AskUserQuestion` —
options: "Post as-is", "Edit first", "Skip". On "Edit first", invite the
user to edit the temp file and re-confirm.

If the user confirms posting:

```bash
bash "${SKILL_DIR}/scripts/tracker-issue-comments.sh" \
    --issue-number "${TRACKER_ISSUE_NUMBER}" \
    --body-file "${BODY_FILE}"
```

## Step 6 — Final summary

Print the consolidated state (one table or block) so the user knows what to
follow up on manually:

```text
ODH llm-d Release — v3.5-ea2

Component                    Branch                 Tag             Release         Quay
inference-scheduler          release-v3.5-ea2  ✓    odh-v3.5-ea2 ✓  draft URL       2/2 found
batch-gateway                release-v3.5-ea2  ✓    odh-v3.5-ea2 ✓  draft URL       3/3 found
workload-variant-autoscaler  release-v3.5-ea2  ✓    odh-v3.5-ea2 ✓  draft URL       1/1 found
llm-d-kv-cache               release-v3.5-ea2  ✓    odh-v3.5-ea2 ✓  draft URL       0/1 found  ⚠ image pending

KServe metadata PR:  <pr-url>
Tracker comment:     <comment-url> (or "skipped")

Follow-ups for the release manager:
- Review and publish each draft GitHub release once notes look right.
- Review the KServe PR and request reviews from KServe maintainers.
- Confirm Konflux UI shows each pipeline run as Succeeded.
- ⚠ Pending Quay images (verify manually — Konflux may still be building, or it failed):
    quay.io/opendatahub/llm-d-kv-cache:v3.5-ea2
    → https://quay.io/repository/opendatahub/llm-d-kv-cache?tab=tags
```

## Scripts (used by the orchestrator and by sub-agents)

The orchestrator calls these directly: `scripts/tools-checker.sh`,
`scripts/tracker-issue-finder.sh`, `scripts/tracker-issue-comments.sh`.

The per-component sub-agent (per `references/per-component-task.md`) calls:
`scripts/create-release-branch.sh`, `scripts/onboarder-trigger-gha.sh`,
`scripts/onboarder-pr-finder.sh`, `scripts/onboarder-pr-validator.sh`,
`scripts/onboarder-pr-merge.sh`, `scripts/release-image-checker.sh`,
`scripts/create-github-release.sh`.

The KServe metadata sub-agent (per `references/kserve-pr-task.md`) calls:
`scripts/open-kserve-metadata-pr.sh`.

All scripts support `--help`.

## Gotchas

- **Sub-agent parallelism is at-most-N.** The harness may serialize if it
  hits rate limits. Sub-agents are independent and idempotent (each
  resource creation script checks-then-creates), so a re-run picks up where
  it left off — never overwrites past work.
- **Konflux runs are asynchronous.** Step 2 inside each per-component
  sub-agent only triggers the workflow; step 3 polls for the resulting PR
  (15 min budget, 1 min interval) and step 6 polls Quay for the image tag
  (15 min budget, 1 min interval). The Quay budget is tunable via the
  sub-agent's `QUAY_TIMEOUT`.
- **PR validation can fail safely.** If the onboarder PR's tekton files
  don't match the expected `output-image`, `path-context`, or `dockerfile`
  for a component, the sub-agent reports the diff and refuses to merge.
  The release manager fixes the registry (or the onboarder), then re-runs.
- **KServe PR uses a fork.** The release manager normally doesn't have
  write access to `opendatahub-io/kserve`; the KServe sub-agent forks
  under the release manager's gh user, pushes there, and opens a
  cross-fork PR against `master`.
- **The skill never publishes the GitHub release.** Releases are created
  as drafts; the release manager publishes manually after reviewing the
  auto-generated notes.
- **The skill never auto-posts the tracker comment.** It composes the
  comment, shows the body, and asks before posting.
