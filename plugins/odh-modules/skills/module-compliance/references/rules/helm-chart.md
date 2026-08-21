---
paths: ["charts/**", "helm/**"]
---

# Module Helm Chart Rules

The Helm chart must contain ONLY module controller infrastructure manifests:

Allowed template kinds:
- Deployment (the controller pod)
- ServiceAccount
- ClusterRole / ClusterRoleBinding / Role / RoleBinding
- CustomResourceDefinition
- ConfigMap (controller config only)
- Service (webhook endpoint only)

Do NOT include application-level manifests -- the workloads this module manages
(e.g., Pods, Services, Routes, Ingresses of the actual application). Those are
embedded in the controller binary and applied by the controller at runtime.

Chart.yaml must have `apiVersion: v2`, `name`, and `version` fields.

values.yaml must provide sensible defaults for all template values so that the
chart renders successfully with zero user configuration.

RBAC rules in ClusterRole templates must use specific verbs and resources. No
wildcards (`"*"`).

Controller Deployment must set:
- Pod-level `securityContext.runAsNonRoot: true`
- Pod-level `securityContext.seccompProfile.type: RuntimeDefault`
- Container-level `securityContext.readOnlyRootFilesystem: true`
- Container-level `securityContext.allowPrivilegeEscalation: false`
- Container-level `securityContext.capabilities.drop: ["ALL"]`
- Health and readiness probes
