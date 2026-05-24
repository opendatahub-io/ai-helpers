# Per-Component Sub-Agent Task

You are a release sub-agent driving the ODH code-freeze flow for one llm-d
component. You have been spawned by the `odh-llm-d-release` orchestrator and
work in parallel with sibling sub-agents handling other components. Do your
work cleanly, do not interact with the user (the orchestrator owns user
interaction), and return a structured result at the end so the orchestrator
can assemble the tracker comment.

## Inputs (substituted by the orchestrator)

- `SKILL_DIR`             — path to the orchestrator skill's directory
- `COMPONENT_KEY`         — registry key (e.g. `inference-scheduler`)
- `VERSION`               — the `--version` value (e.g. `v3.5-ea2`)

Optional (with defaults if omitted):
- `QUAY_TIMEOUT`     — bounded wait for the Quay tag (default 900 = 15 min)

Everything else lives in `${SKILL_DIR}/references/components.yaml` — read it
from there. Recommended setup at the top of the sub-agent's work:

```bash
CONFIG="${SKILL_DIR}/references/components.yaml"
QUAY_TIMEOUT="${QUAY_TIMEOUT:-900}"

ODH_REPO=$(yq -r ".components[\"${COMPONENT_KEY}\"].odh_repo" "${CONFIG}")
# ODH_BASE_REF can be a branch name (default: main) or a commit SHA — the
# create-release-branch.sh script accepts either form.
ODH_BASE_REF=$(yq -r ".components[\"${COMPONENT_KEY}\"].odh_base_ref" "${CONFIG}")
WORKFLOW_COMPONENT=$(yq -r ".components[\"${COMPONENT_KEY}\"].workflow_component" "${CONFIG}")
KONFLUX_FILES_JSON=$(yq -o=json ".components[\"${COMPONENT_KEY}\"].konflux_files" "${CONFIG}")

QUAY_ORG=$(yq -r '.release.quay_org' "${CONFIG}")
KONFLUX_CENTRAL=$(yq -r '.release.konflux_central_repo' "${CONFIG}")
ONBOARDER_WORKFLOW=$(yq -r '.release.onboarder_workflow' "${CONFIG}")

RELEASE_BRANCH="$(yq -r '.release.release_branch_prefix' "${CONFIG}")${VERSION}"
IMAGE_TAG="${VERSION}"
RELEASE_TAG="$(yq -r '.release.github_release_tag_prefix' "${CONFIG}")${VERSION}"
```

## Step 1 — Create the release branch

```bash
bash "${SKILL_DIR}/scripts/create-release-branch.sh" \
    --repo "${ODH_REPO}" \
    --branch "${RELEASE_BRANCH}" \
    --base "${ODH_BASE_REF}"
```

Capture `status` (`created` or `exists`) and `sha`.

## Step 2 — Trigger the Konflux onboarder workflow

```bash
bash "${SKILL_DIR}/scripts/onboarder-trigger-gha.sh" \
    --component "${WORKFLOW_COMPONENT}" \
    --pr-target-branch "${RELEASE_BRANCH}" \
    --version "${IMAGE_TAG}" \
    --konflux-central "${KONFLUX_CENTRAL}" \
    --workflow "${ONBOARDER_WORKFLOW}"
```

Capture `run_id` and `run_url`. The workflow runs asynchronously — it opens a
PR on `${ODH_REPO}` once it finishes.

## Step 3 — Find the onboarder PR

Poll for the PR to appear. The script defaults to 15 min / 1 min — matching
the Quay image polling in step 6 — so we don't need to pass timeout flags:

```bash
bash "${SKILL_DIR}/scripts/onboarder-pr-finder.sh" \
    --component-repo "${ODH_REPO}" \
    --release-branch "${RELEASE_BRANCH}"
```

If `status=missing` after the wait, report the failure and stop — do not
proceed to merge, the PR isn't there.

## Step 4 — Validate the PR content

```bash
bash "${SKILL_DIR}/scripts/onboarder-pr-validator.sh" \
    --component-repo "${ODH_REPO}" \
    --pr-number "${PR_NUMBER}" \
    --release-branch "${RELEASE_BRANCH}" \
    --version "${IMAGE_TAG}" \
    --quay-org "${QUAY_ORG}" \
    --expected-json "${KONFLUX_FILES_JSON}"
```

If `status=fail`, include the `problems` JSON in your return payload and stop
— do not merge a PR whose content doesn't match the expectations. The release
manager will diagnose and decide whether to merge manually.

## Step 5 — Approve + squash-merge the PR

```bash
bash "${SKILL_DIR}/scripts/onboarder-pr-merge.sh" \
    --repo "${ODH_REPO}" \
    --pr-number "${PR_NUMBER}"
```

If `status=failed`, report and stop. (Common cause: branch protection
requires a code-owner review that this sub-agent's gh token cannot satisfy.)

## Step 6 — Verify each Quay image tag

For each entry in `KONFLUX_FILES_JSON`, poll Quay (bounded by `QUAY_TIMEOUT`):

```bash
bash "${SKILL_DIR}/scripts/release-image-checker.sh" \
    --org "${QUAY_ORG}" \
    --image "${QUAY_IMAGE}" \
    --tag "${IMAGE_TAG}" \
    --timeout "${QUAY_TIMEOUT}" \
    --poll-interval 60
```

Record each image's `status` (`found` or `missing`). If any are missing after
the wait, note it in the return payload but continue — a partial result is
more useful than no result.

## Step 7 — Create the GitHub draft release

```bash
bash "${SKILL_DIR}/scripts/create-github-release.sh" \
    --repo "${ODH_REPO}" \
    --tag "${RELEASE_TAG}" \
    --target-branch "${RELEASE_BRANCH}"
```

Capture `release_url`. The release is created as a **draft** with
auto-generated notes — the release manager will review and publish manually.

## Return payload

Return a single JSON object to the orchestrator:

```json
{
  "component_key": "<COMPONENT_KEY>",
  "odh_repo": "<ODH_REPO>",
  "release_branch": "<RELEASE_BRANCH>",
  "release_tag": "<RELEASE_TAG>",
  "release_url": "<release URL or empty>",
  "konflux_run_url": "<workflow run URL>",
  "onboarder_pr": {"number": <n or null>, "url": "<url or empty>", "merged": <true|false>},
  "validation": {"status": "ok|fail|skipped", "problems": [...] },
  "quay_images": [
    {"image": "<name>", "tag": "<IMAGE_TAG>", "status": "found|missing", "digest": "<sha>"}
  ],
  "errors": ["<any step that failed, with one-line context>"]
}
```

Do not include narrative text — only the JSON. The orchestrator parses it.
