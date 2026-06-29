# KServe Metadata PR Sub-Agent Task

You are a sub-agent spawned by the `odh-llm-d-release` orchestrator. Your job
is to open a single PR to `opendatahub-io/kserve` that bumps the upstream
versions for all llm-d components being released this cycle (plus vLLM).
You run in parallel with the per-component sub-agents and do not interact
with the user — the orchestrator owns user interaction.

## Inputs (substituted by the orchestrator)

- `SKILL_DIR`            — Path to the orchestrator skill directory
- `VERSION`              — ODH release version (e.g. `v3.5-ea2`)
- `UPDATES`         — JSON array; each entry has `name` and `version`

The upstream repo and target branch are hardcoded in the script
(`opendatahub-io/kserve@master`). The metadata file path and the keep-list
are read from `${SKILL_DIR}/references/components.yaml` under `release.kserve_*`.

## Step 1 — Open the PR

```bash
CONFIG="${SKILL_DIR}/references/components.yaml"
METADATA_FILE=$(yq -r '.release.kserve_metadata_file' "${CONFIG}")
KEEP=$(yq -r '.release.kserve_keep_entries | join(",")' "${CONFIG}")

bash "${SKILL_DIR}/scripts/open-kserve-metadata-pr.sh" \
    --metadata-file "${METADATA_FILE}" \
    --version "${VERSION}" \
    --updates "${UPDATES}" \
    --keep "${KEEP}"
```

The script:
- Forks the upstream repo into your gh user account (idempotent).
- Clones the fork at the target branch.
- Edits the metadata file: for each entry in `UPDATES`, updates the
  matching `name:` entry's `version:`; if the entry is missing, appends a
  new one.
- Refuses to bump any entry whose name is in `KEEP`.
- Commits, pushes to the fork, opens a cross-fork PR.

## Step 2 — Report

Return a single JSON object:

```json
{
  "kserve_pr": {
    "status": "created|exists|failed",
    "number": <n or null>,
    "url": "<url or empty>"
  },
  "updates_applied": <UPDATES>,
  "errors": ["<any failure with one-line context>"]
}
```

Do not include narrative text — only the JSON. If `status=failed`, include
the reason in `errors`. The orchestrator parses your output.
