---
paths: ["api/**/*.go"]
---

# Module CRD Type Conventions

The CR type must implement `common.PlatformObject` from
`github.com/opendatahub-io/odh-platform-utilities/api/common`. This interface
composes `client.Object`, `WithStatus`, `ConditionsAccessor`, and
`WithReleases`.

Add a compile-time assertion: `var _ common.PlatformObject = (*MyType)(nil)`

Required PlatformObject methods:
- `GetStatus() *common.Status`
- `GetConditions() []common.Condition`
- `SetConditions([]common.Condition)`
- `GetReleaseStatus() *common.ComponentReleaseStatus`
- `SetReleaseStatus(common.ComponentReleaseStatus)`

Status struct must embed `common.Status` and `common.ComponentReleaseStatus`
with `json:",inline"` tags.

CRD must be cluster-scoped with singleton naming enforced via CEL:

```go
// +kubebuilder:resource:scope=Cluster
// +kubebuilder:validation:XValidation:rule="self.metadata.name == 'default-mycomponent'",message="..."
```

User-facing config fields belong in `XxxCommonSpec`, inlined into both
`XxxSpec` and the DSC stanza. Fields only in `XxxSpec` (not in CommonSpec)
must be operator-written only.

Embed `common.ManagementSpec` for Managed/Removed lifecycle. Do NOT import
`github.com/openshift/api` for management state.

Status `Phase` may only use `common.PhaseReady` or `common.PhaseNotReady`.
No custom phase values.

API group must be `components.platform.opendatahub.io` or
`services.platform.opendatahub.io`.

After modifying types, run: `make generate manifests`
