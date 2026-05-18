---
name: module-compliance
description: >-
  Check an ODH module operator repository for contract violations against the
  platform onboarding guide. Validates PlatformObject status, CRD structure,
  Helm chart content, webhook ownership, metadata conventions, and reconciler
  chain ordering. Use during code review or after scaffolding a new module.
allowed-tools: Read Grep Glob
user-invocable: true
argument-hint: "[path to module repo root]"
metadata:
  author: ODH
  version: "1.0"
  tags: "odh, module, compliance, review, operator"
---

# ODH Module Compliance Check

Validate a module operator repository against the ODH platform contract.

## Step 1: Identify the module root

If `$ARGUMENTS` provides a path, use it. Otherwise use the current working
directory.

Verify the directory contains a Go module by checking for `go.mod`. Read
`go.mod` and confirm it imports
`github.com/opendatahub-io/odh-platform-utilities` at version `v0.1.0` or
later. If the import is missing, record a **CRITICAL** finding immediately --
the module must use the shared library, not the operator internal types.

Locate the CRD types directory by searching for files matching
`api/**/types.go` or `api/**/*_types.go`. Locate the controller directory by
searching for files matching `internal/controller/**/*.go`.

## Step 2: Run compliance checks

Load the full rule set from `${CLAUDE_SKILL_DIR}/references/contract.md`.

For each rule, search the codebase using `Grep` and `Read` to determine
pass/fail. Collect results into a list with rule ID, status (PASS / FAIL /
WARN / SKIP), file path and line number for violations, and a short
explanation.

Rules are grouped into these categories:

1. **API contract** -- PlatformObject interface, status fields, mandatory
   conditions, singleton enforcement, API group and version.
2. **Spec conventions** -- CommonSpec pattern, ManagementSpec, platform-managed
   fields, ConfigMap minimality.
3. **Controller patterns** -- Reconciler builder, GC action ordering, condition
   manager setup, dependency handling, observedGeneration.
4. **Helm chart** -- Controller-only manifests, no application resources.
5. **Security & metadata** -- Webhook ownership, cert-manager TLS, metadata
   labels/annotations, RBAC scoping.
6. **Separation of concerns** -- No orchestrator logic, self-contained module.

## Step 3: Report findings

Present results grouped by category. Use this format:

```text
## Module Compliance Report: <module-name>

### API Contract
- [PASS] MC-01 PlatformObject interface implemented
- [FAIL] MC-02 Missing WithReleases implementation (api/v1alpha1/types.go:42)
  → Add GetReleaseStatus() and SetReleaseStatus() methods

### Spec Conventions
...

### Summary
  Total: 18 rules checked
  Passed: 15
  Failed: 2
  Warnings: 1
```

After the report, suggest running `/module-scaffold` if the repo is missing
fundamental structure, or provide specific fix instructions for each failure.
