---
name: aipcc-accel-variant-decomposer
description: |
  Generate the EPIC decomposition for an accelerator variant release targeting
  the AIPCC project. Handles all accelerators (CUDA, ROCm, Gaudi, Neuron, TPU,
  CPU) via a standard lifecycle and Spyre via a conditional path. Supports two
  output modes: artifact files compatible with the epic-creator plugin, and
  direct Jira ticket creation via acli. Use when a STRAT or feature ticket
  describes work for a specific accelerator variant targeting a release
  milestone, or when asked to generate variant lifecycle EPICs. Triggers on:
  "create variant EPICs", "decompose accelerator feature", "generate EPIC
  sequence for CUDA/ROCm/Gaudi/Neuron/TPU/CPU/Spyre", "variant lifecycle",
  "release EPICs for accelerator".
user-invocable: true
allowed-tools: Bash, Read, AskUserQuestion
metadata:
  author: AIPCC
  version: "1.0"
  tags: aipcc, accelerator, epic, jira, decomposition
---

# Accelerator Variant Decomposer

Generate the EPIC decomposition for an accelerator variant release. All
accelerators share a common lifecycle with accelerator-specific templates.
Spyre uses a conditional path that replaces torch/vLLM steps with wheel
collection and index transition steps.

Template definitions live in `references/epic-templates.yaml`. A Python script
at `scripts/generate_epics.py` handles deterministic file generation for both
artifact files and Jira JSON payloads.

## Prerequisites

- `acli` must be installed and authenticated (`acli jira auth`) for Jira mode
- Python 3.10+ with `pyyaml` (`pip install pyyaml`) for the generator script

## Inputs

Collect these from the STRAT/feature ticket or ask the user:

| Parameter | Example | Required | Notes |
|-----------|---------|----------|-------|
| `accelerator` | cuda, rocm, gaudi, neuron, tpu, cpu, spyre | Yes | Lowercase identifier |
| `accel_version` | CUDA 12.9, ROCm 7.2, Gaudi 1.24 | Yes | Display name with version |
| `variant` | cuda12.9-ubi9, spyre-ubi9 | Yes | Base image identifier |
| `torch_version` | 2.10 | Yes (non-Spyre) | Not used for Spyre |
| `vllm_version` | 0.19.1 | Yes (non-Spyre) | Not used for Spyre |
| `release` | 3.5 EA1, 3.4 GA | Yes | Target release milestone |
| `parent_feature` | AIPCC-XXXX | Yes | Parent feature ticket key |
| `hardware_type` | NVIDIA GPU, AMD GPU, Gaudi2 | Yes | For QE/AE validation EPIC |
| `sendnn_constraints` | torch-sendnn>=1.2.0 | No (Spyre only) | Post-release constraints |
| `labels` | rhoai-3.5.EA2 | No | Release-specific Jira label |
| `due_date` | 2026-06-15 | No | EPIC due date (YYYY-MM-DD) |

## Execution Modes

Parse `$ARGUMENTS` for mode flags:

| Flag | Behavior |
|------|----------|
| `--artifact-only` | Generate EPIC artifact files only (epic-creator compatible) |
| `--jira-only` | Create Jira tickets directly via acli (no artifact files) |
| `--both` | Generate artifacts and create Jira tickets (default) |
| `--dry-run` | Show what would be created without executing |

If a Jira ticket key is found in `$ARGUMENTS`, extract parameters from it. Any
remaining arguments are treated as overrides for the parameters above.

## Template Selection

The script auto-selects the template from the accelerator type. Read
`references/epic-templates.yaml` for the full list. Summary:

| Accelerator | Template | EPICs |
|-------------|----------|-------|
| cuda (< 13) | `standard_with_qe` | 4: base images, torch, vLLM, QE validation |
| cuda (>= 13) | `cuda_with_modelopt` | 5: base images, torch, vLLM, Model-Opt, QE validation |
| rocm | `rocm` | 4: stack update, torch, vLLM, AE test plan |
| gaudi | `gaudi` | 3: stack update, torch, vLLM |
| neuron | `standard_with_ae_testplan` | 4: stack update, torch, vLLM, AE testplan |
| tpu | `standard_with_qe` | 4: base images, torch, vLLM, QE validation |
| cpu | `cpu` | 4: stack update, torch, vLLM wheels, multi-arch builds |
| spyre | `spyre` | 5-6: wheel collection, containerfile, RC images, final images (+optional constraints) |

## Procedure

### Step 1: Collect Parameters

If a ticket key is provided (matches pattern `[A-Z]+-[0-9]+`):

```bash
acli jira workitem view <ticket-key> --output json
```

Extract accelerator type, version, release, and other parameters from the
ticket summary and description. If any required parameter is missing, ask the
user.

### Step 2: Preview with Dry Run

Run the generator script in dry-run mode to show the user what will be created:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_epics.py \
    --templates ${CLAUDE_SKILL_DIR}/references/epic-templates.yaml \
    --accelerator <accelerator> \
    --accel-version "<accel_version>" \
    --variant <variant> \
    --release "<release>" \
    --parent-feature <parent_feature> \
    --hardware-type "<hardware_type>" \
    --torch-version <torch_version> \
    --vllm-version <vllm_version> \
    --mode <artifact|jira|both> \
    --dry-run
```

Add `--sendnn-constraints`, `--labels`, `--due-date` if provided.

Present the output to the user and wait for confirmation before proceeding.

### Step 3: Generate Output

Run the same command without `--dry-run`:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_epics.py \
    --templates ${CLAUDE_SKILL_DIR}/references/epic-templates.yaml \
    --accelerator <accelerator> \
    --accel-version "<accel_version>" \
    --variant <variant> \
    --release "<release>" \
    --parent-feature <parent_feature> \
    --hardware-type "<hardware_type>" \
    --torch-version <torch_version> \
    --vllm-version <vllm_version> \
    --mode <mode> \
    --output-dir <output_dir>
```

The script creates:

- **Artifact mode**: `artifacts/epic-tasks/{parent}-decomposition.md` (summary
  with Mermaid DAG) and `artifacts/epic-tasks/{parent}-ENNN.md` per EPIC (YAML
  frontmatter compatible with epic-creator).
- **Jira mode**: `artifacts/epic-tasks/jira/{parent}-ENNN-jira.json` files
  with ADF descriptions and Red Hat Employee security level.

### Step 4: Create Jira Tickets

If the mode includes Jira (`--jira-only` or `--both`), create each ticket:

```bash
acli jira workitem create --from-json <jira-json-file>
```

Create EPICs in template order. On success, `acli` prints the new issue key and
URL. Report all created EPIC keys to the user.

Clean up the temporary JSON files after creation.

## Error Handling

- **acli not found**: Tell the user to install acli and run `acli jira auth`
- **Authentication failure**: Tell the user to run `acli jira auth`
- **Creation failure**: Display the error from acli and suggest checking
  permissions or the parent feature key
- **Missing pyyaml**: Tell the user to run `pip install pyyaml`
- **Unknown accelerator**: The script prints valid options; relay to the user

## Applicability

This skill applies when the input mentions:

- A specific accelerator (CUDA, ROCm, Gaudi, Neuron, TPU, CPU, Spyre)
- A UBI9 base image variant
- A target release milestone (EA1, EA2, GA)
- Work to update the accelerator stack and associated components

It does not apply to:

- Cross-cutting release work (base image publication, delivery squad tasks)
- Infrastructure or tooling EPICs without a fixed template
- Day 0 platform investigations for new hardware
- Product release lifecycle EPICs (RPMs, downstream release, etc.)

$ARGUMENTS
