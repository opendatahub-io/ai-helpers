# Monitoring Component Migration Example

Worked example of analyzing the monitoring service for extraction into a
standalone module. This serves as both documentation and a reference for
validating the migration skill output.

## Component Location

The monitoring service lives under the `services` area:

- **CRD types:** `api/services/v1alpha1/monitoring_types.go`
- **Common types:** `api/services/v1alpha1/monitoring_types.odh.go` and
  `monitoring_types.rhoai.go` (distribution-specific variants)
- **Controller:** `internal/controller/services/monitoring/`
- **API group:** `services.platform.opendatahub.io`
- **Singleton name:** `default-monitoring`

## CRD Analysis

### MonitoringSpec

User-facing fields (belong in CommonSpec):
- `metrics` -- Metrics configuration (replicas, storage, exporters)
- `traces` -- Traces configuration (storage, sampling, TLS, exporters)

These are defined in `MonitoringCommonSpec` (already follows the pattern).

### MonitoringStatus

- Embeds `common.Status` (Phase, ObservedGeneration, Conditions)
- Additional field: `serviceUrl` (string) -- module-specific

### Validations

- Singleton name enforced: `self.metadata.name == 'default-monitoring'`
- Metrics: non-zero replicas require storage
- Traces: non-PV backends require secret; size only for PV
- Custom exporters: max 10, reserved names prohibited

## Controller Analysis

### Files to migrate

- `monitoring.go` -- ServiceHandler implementation
- `monitoring_controller.go` -- Reconciler setup
- `monitoring_controller_actions.go` -- Action functions

### Resources managed

The monitoring controller manages:
- Prometheus / monitoring stack Deployments
- ServiceMonitor resources
- PrometheusRule resources
- ConfigMaps for monitoring configuration
- Services for metrics endpoints

### Embedded manifests

Monitoring manifests are embedded via `go:embed` in
`internal/controller/components/components.go`. These need to move into the
standalone module binary.

### Platform dependencies

- Reads DSCI for certificate configuration
- Reads DSCI for authentication settings
- These become platform-managed fields in the module CR spec

## Webhook Analysis

Check for monitoring-related webhooks:
- Singleton validation (CEL rule already in place)
- Any custom validation webhooks for MonitoringSpec fields

## RBAC Analysis

Module-side RBAC rules needed:
- `services.platform.opendatahub.io/monitorings` -- full CRUD + status/finalizers
- `monitoring.coreos.com/prometheusrules` -- CRUD
- `monitoring.coreos.com/servicemonitors` -- CRUD
- `apps/deployments` -- CRUD (for monitoring stack)
- `core/services` -- CRUD
- `core/configmaps` -- CRUD
- `coordination.k8s.io/leases` -- CRUD (leader election)
- `core/events` -- create, patch

## DSC Field Mappings

| DSC Path | Module CR Path | Type |
|----------|---------------|------|
| `spec.components.monitoring.managementState` | `spec.managementState` | ManagementSpec |
| `spec.components.monitoring.metrics` | `spec.metrics` | MonitoringCommonSpec |
| `spec.components.monitoring.traces` | `spec.traces` | MonitoringCommonSpec |
| DSCI auth config | `spec.auth` (platform-managed) | Orchestrator writes |
| DSCI cert config | `spec.certificates` (platform-managed) | Orchestrator writes |

## Import Path Changes

| Current Import | New Import |
|----------------|-----------|
| `api/common` | `odh-platform-utilities/api/common` |
| `api/services/v1alpha1` | New module's `api/v1alpha1` |
| `internal/controller/status` | `odh-platform-utilities/api/common` (condition constants) |
| `pkg/cluster` | `odh-platform-utilities/pkg/cluster` |
| `openshift/api/operator/v1` | Drop -- use `common.ManagementState` |

## Expected Checklist Output

The migration skill should produce a checklist containing approximately:
- 3 files to extract from `api/services/v1alpha1/`
- 3 files to extract from `internal/controller/services/monitoring/`
- Manifests to move from embedded location
- 1 new Helm chart to create
- 8+ RBAC rules to define
- 5+ DSC field mappings to document
- Platform-managed fields (auth, certs) to add to the module CR spec
- cert-manager setup for any webhook TLS
