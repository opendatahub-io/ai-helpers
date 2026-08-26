---
paths: ["**/*.go", "**/*.yaml"]
---

# Module Security Rules

Admission webhooks for the module CR must be defined and served by this module
controller. Do not delegate webhook ownership to the orchestrator.

Use cert-manager for webhook and internal TLS certificates. Do NOT use
OpenShift serving-cert annotations
(`service.beta.openshift.io/serving-cert-secret-name`).

No wildcard verbs or resources in RBAC rules. Every kubebuilder RBAC marker
and every ClusterRole/Role rule must specify explicit verbs and resources.

Never log secrets, tokens, credentials, or API keys at any verbosity level.
Grep for variable names containing `token`, `password`, `credential`,
`apiKey`, `secret` near log statements.

No `InsecureSkipVerify: true` in non-test code.

Use `labels.ManagedBy` (`components.platform.opendatahub.io/managed-by`) on
all resources managed by the controller. Use `labels.PlatformPartOf` for GC
label selection. Both come from `pkg/metadata`.

The module must NOT contain platform orchestration logic. Do not import or
reference `DataScienceCluster`, `DSCInitialization`, or other orchestrator
types. No imports from `api/datasciencecluster` or `api/dscinitialization`.

ConfigMaps must be strictly minimal -- internal controller flags and image
overrides only. User-configurable settings belong in the CR spec.
Platform-managed settings (auth, certs) belong in platform-managed spec fields.
