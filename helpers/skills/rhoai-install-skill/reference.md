# RHOAI Cluster Setup — Reference

## Version Compatibility

| RHOAI Version | Supported OCP Versions | Channel |
|---|---|---|
| 3.x (latest) | 4.19, 4.20, 4.21 | `stable-3.x` (recommended) or `fast-3.x` |
| 2.25 | 4.16, 4.17, 4.18, 4.19, 4.20 | `stable-2.x` or `fast-2.x` |
| 2.22 *(older)* | 4.16, 4.17, 4.18, 4.19 | `stable-2.x` |
| 2.16 *(older)* | 4.14, 4.16, 4.17, 4.18, 4.19 | `stable-2.x` |

RHOAI 3.x is a **new install only** — no upgrade path from 2.x exists. Fresh install or upgrade within 3.x (e.g. 3.2 → 3.3) is supported.

> **Note**: Versions 2.22 and 2.16 are older releases. Verify current support status before using them.  
> **Last verified**: 2026-03-31. Always re-check [Red Hat OpenShift AI: Supported Configurations](https://access.redhat.com/articles/rhoai-supported-configs) and [RHOAI 3.x Lifecycle](https://access.redhat.com/support/policy/updates/rhoai-sm/lifecycle) before recommending a specific version.

Source: [Red Hat OpenShift AI: Supported Configurations](https://access.redhat.com/articles/rhoai-supported-configs)

## Component Prerequisites Matrix

| RHOAI Component | cert-manager | RHBoK | Connectivity Link | LeaderWorkerSet | Service Mesh 3 | GPU Operators |
|---|---|---|---|---|---|---|
| dashboard | | | | | | |
| workbenches | | | | | | |
| aipipelines | | | | | | |
| kserve | **required** | | | | | |
| kserve + llm-d | **required** | | **required** | **required** | | |
| kueue | **required** | **required** | | | | |
| ray | **required** | **required** | | | | |
| trainingoperator | **required** | **required** | | | | |
| llamastackoperator | **required** | | | | **required** | **required** |
| modelregistry | | | | | | |

## RHOAI User Types

| Type | Group | Permissions |
|---|---|---|
| Data scientist / MLOps | `rhods-users` | Create projects, workbenches, pipelines, model serving — within own projects |
| RHOAI admin | `rhods-admins` | All of above + Settings menu, manage all users' workbenches and pipelines |
| Cluster admin | `cluster-admins` | Automatically gets RHOAI admin. Also manages operators, nodes, cluster config |

By default (without groups configured), **all** authenticated OpenShift users can access RHOAI. Configure `groupsConfig` in `OdhDashboardConfig` to restrict access.

## Troubleshooting

### Kueue Subscription fails with "no operators found in channel stable"

The `kueue-operator` package does not have a plain `stable` channel. Check available channels:

```
oc get packagemanifest kueue-operator -o jsonpath='{range .status.channels[*]}{.name}{"\n"}{end}'
```

Use the `defaultChannel` value (e.g. `stable-v1.3`).

### MCP tool returns "no matches for kind" on newly created CRDs

The Kubernetes MCP server caches API resources. After installing an operator that creates new CRDs, the cache may be stale. Use `oc apply` via the Shell tool as a workaround.

### DSC shows "Argo Workflows controllers are not managed but CRD is missing"

Set `argoWorkflowsControllers.managementState` to `Managed` unless you have your own Argo Workflows instance:

```
oc patch datasciencecluster default-dsc --type=merge \
  -p '{"spec":{"components":{"aipipelines":{"argoWorkflowsControllers":{"managementState":"Managed"}}}}}'
```

### OAuth resource cannot be modified on ROSA HCP

The error "This resource cannot be created, updated, or deleted. Please ask your administrator to modify the resource in the HostedCluster object" means the cluster is ROSA HCP. Identity providers must be managed through the `rosa` CLI or the OCM console at https://console.redhat.com/openshift/.

### User logs in but sees "Access permission needed"

The user is not in any of the `allowedGroups` configured in the dashboard. Add them:

```bash
# Validate the username first (letters, digits, hyphen, underscore, dot, @)
USERNAME="<username>"
[[ "$USERNAME" =~ ^[a-zA-Z0-9._@-]+$ ]] || { echo "Invalid username"; exit 1; }
oc adm groups add-users rhods-users -- "$USERNAME"
```

If groups were just changed, the user must log out and log back in for changes to take effect (session management is separate from authentication).
