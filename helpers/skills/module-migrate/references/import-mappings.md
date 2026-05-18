# Import Path Mappings: ODH Operator to odh-platform-utilities

When migrating a component from the monolithic ODH operator to a standalone
module, all imports from the operator's internal packages must be replaced with
their equivalents in `odh-platform-utilities`.

## Type and Interface Mappings

| Operator Import | Utilities Import | Notes |
|-----------------|-----------------|-------|
| `github.com/opendatahub-io/opendatahub-operator/api/common` | `github.com/opendatahub-io/odh-platform-utilities/api/common` | Same types, but `PlatformObject` now includes `WithReleases` |
| `github.com/opendatahub-io/opendatahub-operator/internal/controller/status` | `github.com/opendatahub-io/odh-platform-utilities/api/common` | Condition constants moved to public API |
| `github.com/opendatahub-io/opendatahub-operator/pkg/cluster` | `github.com/opendatahub-io/odh-platform-utilities/pkg/cluster` | `GetSingleton` error changed: use `errors.Is(err, cluster.ErrNoInstance)` instead of `k8serr.IsNotFound(err)` |
| `github.com/opendatahub-io/opendatahub-operator/pkg/webhook` | `github.com/opendatahub-io/odh-platform-utilities/pkg/webhook` | `DenyCountGtZero` signature changed: now takes `(count, gvk)` instead of `(ctx, cli, gvk, msg)` |
| `github.com/openshift/api/operator/v1` (ManagementState) | `github.com/opendatahub-io/odh-platform-utilities/api/common` | Use `common.ManagementState` (plain string type). Values `"Managed"` and `"Removed"` are wire-compatible. |

## Condition Constants

| Operator Constant | Utilities Constant | Value |
|-------------------|-------------------|-------|
| `status.ConditionTypeReady` | `common.ConditionTypeReady` | `"Ready"` |
| `status.ConditionTypeProvisioningSucceeded` | `common.ConditionTypeProvisioningSucceeded` | `"ProvisioningSucceeded"` |
| `status.ConditionTypeDegraded` | `common.ConditionTypeDegraded` | `"Degraded"` |

These were in `internal/controller/status/status.go` (not importable
externally). Now in `api/common`.

## Phase Constants

| Operator Constant | Utilities Constant | Value |
|-------------------|-------------------|-------|
| `status.PhaseReady` | `common.PhaseReady` | `"Ready"` |
| `status.PhaseNotReady` | `common.PhaseNotReady` | `"Not Ready"` |

Also moved from `internal/` to `api/common`.

## Interface Changes

### PlatformObject

The operator's `PlatformObject` did not include `WithReleases`:

```go
// Old (operator)
type PlatformObject interface {
    client.Object
    WithStatus
    ConditionsAccessor
}
```

The utilities version adds `WithReleases`:

```go
// New (utilities -- api/common)
type PlatformObject interface {
    client.Object
    WithStatus
    ConditionsAccessor
    WithReleases
}
```

**Migration action:** Implement `GetReleaseStatus()` and `SetReleaseStatus()`
on the module CR type. Return an empty `ComponentReleaseStatus` if the module
has no sub-components.

### WithReleases

The return type changed:

```go
// Old
GetReleaseStatus() *[]ComponentRelease

// New
GetReleaseStatus() *ComponentReleaseStatus
SetReleaseStatus(status ComponentReleaseStatus) // by value, not pointer
```

### Release (framework)

The reconciler accepts a `Release` struct from `framework/api`, separate from
the CR's `ComponentReleaseStatus`. Pass it via `reconciler.WithRelease()`:

```go
// framework/api
type Release struct {
    Name    Platform       // e.g. "Open Data Hub"
    Version semver.Version
}
```

## Utility Package Mappings

| Purpose | Operator Location | Utilities Package |
|---------|-------------------|-------------------|
| Reconciler setup | Internal reconciler logic | `framework/controller/reconciler` (NewReconciler with options) |
| Condition management | Various internal helpers | `framework/controller/conditions` (Manager) |
| Resource deployment (SSA) | Internal deploy logic | `framework/controller/actions/deploy` |
| Garbage collection | Internal GC logic | `framework/controller/actions/gc` |
| Dynamic ownership | Internal GC logic | `framework/controller/actions/dynamicownership` |
| Helm rendering | Internal render logic | `framework/controller/actions/render` |
| Reconciliation types | Internal types | `framework/controller/types` (ReconciliationRequest) |
| Release info | Internal types | `framework/api` (Release struct) |
| Predicates | Internal predicates | `framework/controller/predicates` |
| Cluster/platform detection | `pkg/cluster` | `pkg/cluster` (same API, unstructured client) |
| OpenShift detection | Various internal helpers | `pkg/cluster/openshift` |
| OLM queries | Various internal helpers | `pkg/cluster/olm` |
| Labels and annotations | Various internal constants | `pkg/metadata/labels`, `pkg/metadata/annotations` |
| Resource helpers | Various internal helpers | `pkg/resources` |

## Dependencies to Remove

After migration, the module's `go.mod` should NOT contain:

- `github.com/opendatahub-io/opendatahub-operator` (no operator dependency)
- `github.com/openshift/api` (management state is now a plain string)

## Migration Verification

After updating imports, run:

```bash
grep -rn "opendatahub-operator/internal" .
grep -rn "openshift/api" .
```

Both commands should return no results. If they do, those imports still need
migration.
