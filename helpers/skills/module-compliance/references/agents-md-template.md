# <COMPONENT_PASCAL> Module Operator

This repository implements a standalone module controller for the
[Open Data Hub](https://opendatahub.io/) platform.

## Architecture Context

The ODH platform follows a hub-and-spoke architecture. The ODH Operator
(orchestrator) deploys module controllers and reads their CR status via the
`PlatformObject` interface. This module is a spoke -- it owns the full
lifecycle of its component and reports status back to the orchestrator.

Reference documents:
- [PlatformObject Contract](https://github.com/opendatahub-io/odh-platform-utilities/blob/main/docs/platform-object-contract.md)
- [Migration Guide](https://github.com/opendatahub-io/odh-platform-utilities/blob/main/docs/migration-from-operator.md)

## Shared Library

All types and utilities must be imported from
`github.com/opendatahub-io/odh-platform-utilities`. Do NOT import from
`github.com/opendatahub-io/opendatahub-operator/internal/` or from
`github.com/openshift/api`.

Key packages:

| Package | Purpose |
|---------|---------|
| `api/common` | PlatformObject interface, Status, Condition, ManagementSpec, ComponentRelease |
| `framework/api` | Release struct, type aliases |
| `framework/controller/reconciler` | NewReconciler with functional options |
| `framework/controller/conditions` | Condition Manager with automatic aggregation |
| `framework/controller/actions/deploy` | SSA-based resource deployment |
| `framework/controller/actions/gc` | Garbage collection of stale resources |
| `framework/controller/actions/render` | Helm/Kustomize manifest rendering |
| `framework/controller/actions/dynamicownership` | Dynamic resource ownership tracking |
| `framework/controller/predicates` | Event filtering predicates |
| `framework/controller/types` | ReconciliationRequest type |
| `pkg/cluster` | Platform detection (OpenShift, FIPS, SNO) |
| `pkg/webhook` | Singleton admission webhook helpers |
| `pkg/metadata/labels` | Platform label constants (ManagedBy, PlatformPartOf) |
| `pkg/metadata/annotations` | Platform annotation constants |
| `pkg/resources` | Resource decode, hash, apply, sort utilities |

## CRD Rules (`api/**/*.go`)

- The CR type must implement `common.PlatformObject` (includes `WithReleases`).
  Add a compile-time assertion: `var _ common.PlatformObject = (*<Type>)(nil)`
- The status struct must embed `common.Status` and
  `common.ComponentReleaseStatus` with `json:",inline"` tags.
- The CRD must be cluster-scoped (`+kubebuilder:resource:scope=Cluster`).
- The singleton name must be enforced via CEL:
  `+kubebuilder:validation:XValidation:rule="self.metadata.name == 'default-<component>'"`.
- The API group must be `components.platform.opendatahub.io` or
  `services.platform.opendatahub.io`.
- User-facing fields belong in `<Type>CommonSpec`, inlined into both
  `<Type>Spec` and the DSC stanza. Fields only in `<Type>Spec` (not in
  CommonSpec) must be operator-written only.
- Embed `common.ManagementSpec` for Managed/Removed lifecycle. This is a
  plain `string` type -- do NOT import `github.com/openshift/api` for it.
- Platform-managed fields (auth, certs, monitoring) must be spec fields, not
  ConfigMap entries.
- Status `Phase` may only be `common.PhaseReady` ("Ready") or
  `common.PhaseNotReady` ("Not Ready"). No custom phase values.

## Controller Rules (`internal/controller/**/*.go`)

- Use `reconciler.NewReconciler` from `framework/controller/reconciler` with
  functional options.
- Three mandatory actions: render, deploy, gc. **GC must be the last action**
  added via `AddAction()`. Deploy stamps annotations that GC reads -- reversing
  the order deletes resources that were just deployed.
- Configure conditions via `WithConditionsManagerFactory` with:
  - `ConditionTypeReady` as the happy condition
  - `ConditionTypeProvisioningSucceeded` as a dependent (MUST aggregate into Ready)
  - `ConditionTypeDegraded` as a dependent (COULD aggregate depending on severity)
- Every condition update must include `ObservedGeneration` set from the CR's
  `.metadata.generation`.
- Update `status.observedGeneration = cr.Generation` on every reconcile.
- Handle missing dependencies gracefully via conditions (`Degraded=True` or
  `Ready=False` with clear Reason). Never crash or `os.Exit` on a missing
  dependency.
- Use `framework/controller/actions/deploy` for SSA-based resource deployment.
  Use `framework/controller/actions/render` for manifest rendering.
- Use `pkg/cluster` for environment detection (OpenShift, FIPS, etc.). The
  module performs its own detection -- it does not rely on the orchestrator.

## Helm Chart Rules (`charts/**`)

- The chart must contain ONLY module controller manifests: Deployment,
  ServiceAccount, ClusterRole, ClusterRoleBinding, CRD, ConfigMap (controller
  config only), Service (webhook only).
- Do NOT include application-level manifests (the workloads this module
  manages). Those are embedded in the controller binary and applied at runtime.
- `Chart.yaml` must have `apiVersion: v2`, `name`, and `version` fields.
- `values.yaml` must provide sensible defaults for all template values.

## Security Rules

- All admission webhooks must be defined and served by this module, not
  delegated to the orchestrator.
- Use cert-manager for webhook and internal TLS certificates. Do NOT use
  OpenShift serving-cert annotations
  (`service.beta.openshift.io/serving-cert-secret-name`).
- No wildcard verbs or resources in RBAC rules. Every ClusterRole/Role rule
  must specify explicit verbs and resources.
- Never log secrets, tokens, credentials, or API keys at any verbosity level.
- Use `labels.ManagedBy` (`components.platform.opendatahub.io/managed-by`)
  on all managed resources. Use `labels.PlatformPartOf` for GC label selection.

## Separation of Concerns

- This module must NOT contain platform orchestration logic. Do not import or
  reference `DataScienceCluster`, `DSCInitialization`, or other orchestrator
  types.
- The module must be self-contained: controller logic, webhooks, RBAC, CRDs,
  manifests, and monitoring rules all live in this repository.
- ConfigMaps must be strictly minimal -- only internal controller flags and
  image overrides. User-configurable settings belong in the CR spec.
  Platform settings belong in platform-managed spec fields.

## Testing

- Use `fake.NewClientBuilder()` with explicit scheme registration for unit
  tests. Register schemes via a shared test helper.
- E2E test oracles must be structurally independent from production code.
  Never call the same production function or read the same API resource as the
  code under test.
- Use `t.Parallel()` in all tests and subtests.
- Use table-driven tests for variations.

## Code Review Checklist

When reviewing code in this repository, always verify:

1. No imports from `opendatahub-operator/internal/` or `openshift/api`
2. Status conditions include `ObservedGeneration`
3. GC action is last in the reconciler chain
4. No `InsecureSkipVerify: true` in non-test code
5. No wildcard RBAC rules
6. No secrets/tokens in log statements
7. Helm chart contains only controller manifests
8. Platform-managed fields are in spec, not ConfigMap
