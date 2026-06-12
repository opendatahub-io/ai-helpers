# ODH Module Compliance Rules

Library: [odh-platform-utilities](https://github.com/opendatahub-io/odh-platform-utilities)

Target library version: v0.x (pre-v1)

---

## Category 1: API Contract

### MC-01 PlatformObject interface

**What:** The module CR type must implement `common.PlatformObject` from
`github.com/opendatahub-io/odh-platform-utilities/api/common`.

**How to check:**
- Grep for `var _ common.PlatformObject = (*` in `api/` files.
- Verify the type has methods: `GetStatus() *common.Status`,
  `GetConditions() []common.Condition`, `SetConditions([]common.Condition)`,
  `GetReleaseStatus() *common.ComponentReleaseStatus`,
  `SetReleaseStatus(common.ComponentReleaseStatus)`.

**Pass:** Compile-time assertion and all five methods present.
**Fail:** Missing assertion or any method absent.

### MC-02 Status fields

**What:** The module CR status struct must embed `common.Status` and
`common.ComponentReleaseStatus` inline.

**How to check:**
- Read the status struct definition. Look for `common.Status` and
  `common.ComponentReleaseStatus` with `` `json:",inline"` `` tags.

**Pass:** Both embedded inline.
**Fail:** Missing either embed, or using custom fields instead of the shared
types.

### MC-03 Mandatory conditions

**What:** The controller must set three mandatory conditions: `Ready`,
`ProvisioningSucceeded`, `Degraded`.

**How to check:**
- Grep for `common.ConditionTypeReady`, `common.ConditionTypeProvisioningSucceeded`,
  `common.ConditionTypeDegraded` in controller code.
- Alternatively grep for the string literals `"Ready"`,
  `"ProvisioningSucceeded"`, `"Degraded"` used as condition types.

**Pass:** All three condition types referenced in controller logic.
**Fail:** Any mandatory condition type missing.

### MC-04 ObservedGeneration

**What:** Every condition update must include `ObservedGeneration` set from
the CR's `.metadata.generation`.

**How to check:**
- Grep for `ObservedGeneration` in condition-setting code.
- Grep for `WithObservedGeneration` if using the conditions Manager.
- Flag any `Condition{}` literal that omits `ObservedGeneration`.

**Pass:** All condition updates include observed generation.
**Fail/Warn:** Any condition created without `ObservedGeneration`.

### MC-05 Phase values

**What:** The status `Phase` field must only use `common.PhaseReady` ("Ready")
or `common.PhaseNotReady` ("Not Ready"). No custom phase values.

**How to check:**
- Grep for `Phase:` or `.Phase =` assignments in controller code.
- Verify values are `common.PhaseReady` or `common.PhaseNotReady`.

**Pass:** Only standard phase constants used.
**Fail:** Custom phase values like `"Initializing"` or `"Error"`.

### MC-06 Cluster-scoped singleton

**What:** The CRD must be cluster-scoped with a singleton name enforced via
CEL validation.

**How to check:**
- Grep for `+kubebuilder:resource:scope=Cluster` on the CR type.
- Grep for `+kubebuilder:validation:XValidation:rule=` with a
  `self.metadata.name ==` pattern.

**Pass:** Both markers present.
**Fail:** Missing scope marker or missing CEL name validation.

### MC-07 API group

**What:** The CRD must use `components.platform.opendatahub.io` or
`services.platform.opendatahub.io` as its API group.

**How to check:**
- Read `groupversion_info.go` in the API package. Check the `GroupVersion`
  variable's `Group` field.

**Pass:** Group matches one of the two allowed patterns.
**Fail:** Custom or incorrect API group.

### MC-08 API version matches support level

**What:** The API version must match the module's support level:
`v1alpha1` (dev preview), `v1beta1` (tech preview), `v1` (GA).

**How to check:**
- Read the API version directory name and `groupversion_info.go`.

**Pass:** Version follows the convention.
**Warn:** Cannot determine support level automatically; note for manual review.

---

## Category 2: Spec Conventions

### MC-09 CommonSpec pattern

**What:** User-facing configuration fields must be in a `XxxCommonSpec` struct
that is inlined into both the module `XxxSpec` and the DSC stanza.

**How to check:**
- Grep for `CommonSpec` in the API types file.
- Verify the spec struct embeds `XxxCommonSpec` with `` `json:",inline"` ``.

**Pass:** CommonSpec pattern used with inline embedding.
**Warn:** No CommonSpec found -- acceptable if the module has no user-facing
config, but flag for review.

### MC-10 ManagementSpec

**What:** The spec must embed `common.ManagementSpec` (Managed/Removed).
Must NOT import `github.com/openshift/api` for management state.

**How to check:**
- Grep for `common.ManagementSpec` in the spec struct.
- Grep `go.mod` and all `.go` files for `openshift/api` imports.

**Pass:** Uses `common.ManagementSpec`, no `openshift/api` dependency.
**Fail:** Missing ManagementSpec or importing `openshift/api`.

### MC-11 Platform-managed fields

**What:** Fields populated by the orchestrator (auth, certs, monitoring) must
be exposed as spec structs, not sourced from ConfigMaps.

**How to check:**
- If the module references auth or certificate configuration, verify these are
  spec fields, not ConfigMap reads.

**Pass:** Platform settings are spec fields.
**Fail:** Platform settings read from ConfigMap instead of spec.

### MC-12 ConfigMap minimality

**What:** ConfigMaps must be strictly minimal -- only internal controller flags
and image overrides. No user-configurable settings or platform settings.

**How to check:**
- Find ConfigMap definitions in manifests and code. Review their data keys.
- Flag any ConfigMap key that duplicates a spec field or contains
  user-configurable settings.

**Pass:** ConfigMap contains only internal flags.
**Warn:** ConfigMap keys that may belong in the spec instead.

---

## Category 3: Controller Patterns

### MC-13 Condition Manager setup

**What:** The controller should configure a conditions Manager via
`WithConditionsManagerFactory` (or `conditions.NewManager`) with `Ready` as
the happy condition and `ProvisioningSucceeded` and `Degraded` as dependents.

**How to check:**
- Grep for `WithConditionsManagerFactory` or `conditions.NewManager` in
  controller code.
- Verify `ConditionTypeReady` is the happy condition.
- Verify `ConditionTypeProvisioningSucceeded` and `ConditionTypeDegraded` are
  registered as dependents.

**Pass:** Manager configured with correct condition hierarchy.
**Warn:** Manual condition management instead of Manager (functional but
error-prone).

### MC-14 GC action ordering

**What:** The garbage collection action must be the last action added to the
reconciler.

**How to check:**
- Find the reconciler setup (grep for `NewReconciler` or `AddAction`).
- Verify the last `AddAction(...)` call is the GC action.

**Pass:** GC action is last.
**Fail:** GC action is not last, or GC action is missing entirely.

### MC-15 Dependency handling

**What:** Dependencies on other modules must be discovered dynamically via the
Kubernetes API and handled gracefully through conditions.

**How to check:**
- If the module references other module CRs, verify it handles missing
  dependencies by setting `Degraded=True` or `Ready=False` with a clear
  `Reason`, rather than crashing.
- Grep for `panic`, `os.Exit`, or `log.Fatal` in dependency-checking code.

**Pass:** Dependencies handled via conditions, no hard crashes.
**Fail:** Controller crashes on missing dependency.

### MC-16 ObservedGeneration update

**What:** The controller must update `status.observedGeneration` to match
`.metadata.generation` on every successful reconciliation.

**How to check:**
- Grep for `ObservedGeneration` assignment in the reconcile loop or status
  update code.

**Pass:** ObservedGeneration updated from `.metadata.generation`.
**Fail:** ObservedGeneration never set or set to a hardcoded value.

### MC-17 odh-platform-utilities imports

**What:** The module must import types and utilities from
`github.com/opendatahub-io/odh-platform-utilities`, not from the operator's
internal packages.

**How to check:**
- Grep all `.go` files for imports containing
  `opendatahub-io/opendatahub-operator/internal`.
- Grep `go.mod` for `opendatahub-operator` as a dependency.

**Pass:** No imports from operator internals.
**Fail:** Any import from `opendatahub-operator/internal/`.

---

## Category 4: Helm Chart

### MC-18 Controller-only manifests

**What:** The Helm chart must contain only module controller manifests:
Deployment, ServiceAccount, RBAC (ClusterRole, ClusterRoleBinding), CRD.
No application-level manifests (e.g., the actual workload Pods, Services,
Routes, Ingresses that the module manages).

**How to check:**
- List all template files under `charts/` or `helm/`.
- Verify each template is one of: Deployment, ServiceAccount, ClusterRole,
  ClusterRoleBinding, Role, RoleBinding, CustomResourceDefinition,
  ConfigMap (for controller config only), Service (for webhook only).
- Flag any template containing application workload kinds.

**Pass:** Only controller infrastructure manifests.
**Fail:** Application-level manifests in the chart.

### MC-19 Chart structure

**What:** The Helm chart must have a valid `Chart.yaml` with name and version,
a `values.yaml` with defaults, and templates in `templates/`.

**How to check:**
- Verify `Chart.yaml`, `values.yaml`, and `templates/` directory exist.
- Verify `Chart.yaml` has `name`, `version`, and `apiVersion: v2` fields.

**Pass:** Valid chart structure.
**Fail:** Missing required chart files.

---

## Category 5: Security & Metadata

### MC-20 Webhook ownership

**What:** All admission webhooks for the module CR must be defined and served
by the module controller, not delegated to the orchestrator.

**How to check:**
- Grep for `admissionregistration.k8s.io` or webhook setup code.
- Verify webhook server registration is in the module controller's `main.go`
  or controller setup, not in an external project.

**Pass:** Webhooks defined in the module.
**Fail:** No webhook setup found when the CRD requires validation, or
webhooks reference an external service.

### MC-21 cert-manager for TLS

**What:** Internal TLS certificates (for webhooks, mTLS) must use cert-manager.
Must not depend on OpenShift serving-cert annotations.

**How to check:**
- Grep for `cert-manager.io` in manifests and code.
- Grep for `service.beta.openshift.io/serving-cert-secret-name` -- this
  annotation must NOT be used.

**Pass:** cert-manager used for certificate provisioning.
**Fail:** OpenShift serving-cert annotation found.
**Skip:** Module has no webhook or internal TLS requirement.

### MC-22 Metadata conventions

**What:** The module must use platform metadata labels and annotations from
`pkg/metadata`:
- `components.platform.opendatahub.io/managed-by` label (ManagedBy)
- `platform.opendatahub.io/part-of` label (PlatformPartOf)
- Management state annotation

**How to check:**
- Grep for `labels.ManagedBy` or the literal label key in manifests and code.
- Grep for `labels.PlatformPartOf` or the literal label key.

**Pass:** Required labels used.
**Warn:** Recommended labels missing.

### MC-23 RBAC scoping

**What:** No wildcard verbs or resources in RBAC rules.

**How to check:**
- Grep for `"*"` in ClusterRole/Role manifests and kubebuilder RBAC markers.
- Grep for `+kubebuilder:rbac:` markers with `verbs=*` or `resources=*`.

**Pass:** All RBAC rules use specific verbs and resources.
**Fail:** Wildcard RBAC found.

### MC-24 No secrets in logs

**What:** Secrets, tokens, and credentials must never be logged at any
verbosity level.

**How to check:**
- Grep for logging statements that reference secret-related variable names
  (token, password, credential, apiKey, secret).

**Pass:** No secrets in log statements.
**Fail:** Potential secret logged.

---

## Category 6: Separation of Concerns

### MC-25 No orchestrator logic

**What:** The module must not contain platform orchestration logic. It must not
import or reference `DataScienceCluster`, `DSCInitialization`, or other
platform CRs from the orchestrator.

**How to check:**
- Grep for `DataScienceCluster`, `DSCInitialization`, `DSCI` in module code.
- Grep for imports from `api/datasciencecluster` or `api/dscinitialization`.

**Pass:** No orchestrator references.
**Fail:** Module contains orchestrator logic.

### MC-26 Self-contained module

**What:** All pieces of the module must move together: controller logic,
webhooks, RBAC, CRDs, manifests, and monitoring rules. Nothing should be
split across the orchestrator.

**How to check:**
- Verify the module repo contains: CRD types, controller, webhook (if needed),
  RBAC definitions, Helm chart with all controller manifests.
- Check that no controller logic for this module exists in the orchestrator.

**Pass:** All components present in the module repo.
**Warn:** Cannot verify orchestrator-side without access to that repo.

### MC-27 Environment detection in module

**What:** Smart behavior (FIPS detection, disconnected environment handling,
cluster type detection) must be in the module controller, not expected from the
orchestrator.

**How to check:**
- If the module has environment-specific behavior, verify it uses
  `pkg/cluster` for detection rather than reading values passed by the
  orchestrator.

**Pass:** Module performs its own environment detection.
**Skip:** Module has no environment-specific behavior.
