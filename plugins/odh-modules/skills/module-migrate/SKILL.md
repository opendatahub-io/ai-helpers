---
name: module-migrate
description: >-
  Read existing in-tree ODH operator component code and produce a step-by-step
  extraction checklist for migrating it to a standalone module. Analyzes
  controller logic, webhooks, RBAC, embedded manifests, and DSC field mappings.
  Use when extracting a component from the monolithic operator into its own
  module repo.
allowed-tools: Read Grep Glob Write
user-invocable: true
disable-model-invocation: true
argument-hint: "<component-name>"
metadata:
  author: ODH
  version: "1.0"
  tags: "odh, module, migration, operator, extraction"
---

# ODH Module Migration

Analyze an in-tree ODH operator component and generate a migration checklist
for extracting it into a standalone module operator.

## Prerequisites

The user must have the `opendatahub-io/opendatahub-operator` repository (or a
fork) checked out locally. This skill reads that codebase to analyze the
component.

## Step 1: Identify the component

Extract the component name from `$ARGUMENTS`. If not provided, ask the user.

Search for the component in these locations within the operator repo:

- `internal/controller/components/<name>/` (component controllers)
- `internal/controller/services/<name>/` (service controllers)
- `api/components/v1alpha1/<name>_types.go` (component CRD types)
- `api/services/v1alpha1/<name>_types.go` (service CRD types)

If the component is found under `components/`, the target API group is
`components.platform.opendatahub.io`. If under `services/`, use
`services.platform.opendatahub.io`.

## Step 2: Analyze controller logic

Read all files in the component's controller directory. Document:

1. **Handler implementation** -- the file implementing the handler interface
   (ComponentHandler or ServiceHandler). Note which interface methods are
   implemented.
2. **Controller setup** -- how the reconciler is registered. Note if it uses
   the builder pattern or a legacy pattern.
3. **Action functions** -- list each action (render, deploy, gc, custom) and
   what it does.
4. **Resources managed** -- grep for resource kinds the controller
   creates/updates (Deployments, Services, ConfigMaps, Routes, etc.).
5. **Embedded manifests** -- look for `go:embed` directives, template files,
   or inline YAML strings. Note their locations.
6. **Platform dependencies** -- grep for references to DSCI, DSC, or other
   platform CRs within the controller logic.

## Step 3: Analyze CRD types

Read the component's CRD types file. Document:

1. **Spec fields** -- list all spec fields. Identify which are user-facing
   (belong in CommonSpec) vs operator-written (stay in Spec only).
2. **Status fields** -- check if it already implements PlatformObject or uses
   a different status pattern.
3. **Platform-managed fields** -- fields populated by the orchestrator (auth,
   certs, monitoring config).
4. **Validation** -- CEL rules, webhook validations, enum constraints.

## Step 4: Analyze webhooks

Search for webhook registrations related to the component using the Grep
tool:

- Search for `"webhook"` in `internal/controller/components/<name>/`
- Search for `"webhook"` in `internal/controller/services/<name>/`
- Search for `"<ComponentKind>"` in `internal/webhook/`

Document each webhook: type (validating/mutating), what it validates, where
the handler code lives.

## Step 5: Analyze RBAC

Find RBAC requirements for the component:

1. Check for `+kubebuilder:rbac:` markers in the controller files.
2. Check top-level controller RBAC files that may cover this component's
   operations (e.g., `internal/controller/datasciencecluster/kubebuilder_rbac.go`).
3. List each RBAC rule: apiGroup, resource, verbs.
4. Separate rules into:
   - **Module-side** -- rules the standalone module controller needs
   - **Orchestrator-side** -- rules the orchestrator needs to manage the module

## Step 6: Analyze DSC/DSCI field mappings

Find how the component's configuration flows from DSC to the component:

1. Grep for `spec.components.<name>` or the component's stanza name in the
   DSC types.
2. Read the DSC-to-component mapping code. Note which DSC fields map to which
   component spec fields.
3. Identify platform-wide settings from DSCI (auth, certs, monitoring) that
   are injected into the component.

## Step 7: Map import paths

Using `${CLAUDE_SKILL_DIR}/references/import-mappings.md`, identify all
imports from the operator's internal packages and map them to their
`odh-platform-utilities` equivalents.

Use the Grep tool to find imports that need remapping:

- Search for `"opendatahub-operator"` in `internal/` and `api/`
- Search for `"openshift/api"` in `internal/` and `api/`

For each import, note the old path, the new path, and any API changes
(e.g., `WithReleases` is now part of PlatformObject).

## Step 8: Generate migration checklist

Write the checklist to `migration-checklist-<component>.md` in the current
directory. Use this structure:

```markdown
# Migration Checklist: <Component> Module

Generated from opendatahub-operator analysis on <YYYY-MM-DD>.

## 1. Create Module Repository

- [ ] Create repo: `opendatahub-io/<component>-operator`
- [ ] Run `/module-scaffold <component>` to generate the skeleton
- [ ] Initialize go.mod with `github.com/opendatahub-io/<component>-operator`

## 2. Migrate CRD Types

- [ ] Move types from `api/<area>/v1alpha1/<component>_types.go`
- [ ] Create CommonSpec with user-facing fields: <list fields>
- [ ] Move operator-written fields to Spec only: <list fields>
- [ ] Implement PlatformObject interface (including WithReleases)
- [ ] Replace `operatorv1.ManagementState` with `common.ManagementState`
- [ ] Add CEL singleton validation for name `default-<component>`
- [ ] Replace status type with common.Status + ComponentReleaseStatus embeds

## 3. Migrate Controller Logic

- [ ] Move handler from `internal/controller/<area>/<component>/`
- [ ] Adapt to standalone reconciler builder pattern
- [ ] Replace operator-internal imports with odh-platform-utilities:
      <list each import mapping>
- [ ] Extract render action (embed manifests in module binary)
- [ ] Extract deploy action (use pkg/deploy Deployer)
- [ ] Add gc action as LAST action in builder chain
- [ ] Set up condition Manager (Ready + ProvisioningSucceeded + Degraded)
- [ ] Add observedGeneration update on every reconcile

## 4. Migrate Manifests

- [ ] Move embedded manifests from `opt/manifests/<component>/` to module
- [ ] Package application manifests inside the controller binary
- [ ] Create Helm chart with controller-only manifests (Deployment, RBAC, CRD)

## 5. Migrate Webhooks

- [ ] Move webhook handlers: <list each webhook>
- [ ] Add singleton webhook using pkg/webhook
- [ ] Configure cert-manager for webhook TLS (not OpenShift serving-cert)

## 6. Migrate RBAC

- [ ] Module RBAC rules: <list rules>
- [ ] Remove component-specific RBAC from orchestrator's ClusterRole

## 7. Handle Dependencies

- [ ] <list each dependency and handling strategy>

## 8. Platform Integration

- [ ] Document DSC field mappings for orchestrator integration:
      <list DSC field → module spec field mappings>
- [ ] Document DSCI platform config injection points:
      <list DSCI fields that get projected into module CR>
- [ ] Create ConfigMap template for internal flags

## 9. Testing

- [ ] Move/adapt unit tests from operator repo
- [ ] Create E2E tests for standalone deployment
- [ ] Verify Helm chart deploys correctly
- [ ] Run `/module-compliance` to validate contract

## 10. Cleanup

- [ ] Remove component code from operator repo
- [ ] Remove component RBAC from operator ClusterRole
- [ ] Add module registration in operator's module registry
- [ ] Update operator's DSC reconciler to use ModuleHandler
```

Customize each section with the specific details discovered in Steps 2-7.
Replace placeholder `<list ...>` items with actual file paths, field names,
import paths, and RBAC rules found during analysis.

## Gotchas

- The operator's `PlatformObject` interface did not include `WithReleases`.
  The shared library version does. Every migrated CR must implement
  `GetReleaseStatus()` and `SetReleaseStatus()`.
- `GetSingleton` error handling changed: use `errors.Is(err, cluster.ErrNoInstance)`
  instead of `k8serr.IsNotFound(err)`.
- `DenyCountGtZero` signature changed: now takes `(count, gvk)` instead of
  `(ctx, cli, gvk, msg)`. Counting is done separately via `CountObjects`.
- Embedded manifests in the operator are shared across components via
  `go:embed` in `components.go`. The migration must extract only the
  manifests for the target component.
- Some RBAC rules in the operator cover multiple components. Split them
  carefully -- the module only needs rules for its own resources.
- The operator uses `operatorv1.ManagementState` from `openshift/api`. The
  shared library uses a plain `string` type. The JSON values are identical
  so CRDs do not need regeneration for this field.

## Step 9: Summary

Present a brief summary to the user:

- Number of files to migrate
- Key architectural changes needed
- Risks or areas needing manual review
- Suggest running `/module-scaffold <component>` first, then applying the
  checklist to fill in the component-specific logic
