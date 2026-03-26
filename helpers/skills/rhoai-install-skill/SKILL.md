---
name: rhoai-cluster-setup
description: >-
  Install and configure Red Hat OpenShift AI on an OpenShift cluster, including
  all prerequisites (cert-manager, Red Hat build of Kueue) and user/group setup.
  Use when the user asks to install RHOAI, set up OpenShift AI, configure an AI
  platform on OpenShift, or provision a data science cluster.
---

# RHOAI Cluster Setup

Automates the full installation of Red Hat OpenShift AI Self-Managed on an OpenShift cluster. Follows the official docs and handles version compatibility, prerequisite operators, DataScienceCluster creation, and user/group configuration.

## Official Documentation

Always verify steps against the current docs before executing:

- **Install guide**: `https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/<VERSION>/html/installing_and_uninstalling_openshift_ai_self-managed/installing-and-deploying-openshift-ai_install`
- **Distributed workloads**: `https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/<VERSION>/html/installing_and_uninstalling_openshift_ai_self-managed/installing-the-distributed-workloads-components_install`
- **User management**: `https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/<VERSION>/html/managing_openshift_ai/managing-users-and-groups`
- **RHBoK**: `https://docs.redhat.com/en/documentation/openshift_container_platform/<OCP_VERSION>/html/ai_workloads/red-hat-build-of-kueue`
- **cert-manager**: `https://docs.redhat.com/en/documentation/openshift_container_platform/<OCP_VERSION>/html/security_and_compliance/cert-manager-operator-for-red-hat-openshift`

Replace `<VERSION>` and `<OCP_VERSION>` with the target versions.

## Phase 1: Prerequisites Check

Before installing anything, validate the cluster. **Stop and inform the user** if any check fails.

### 1.1 Cluster version

```
oc get clusterversion version -o jsonpath='{.status.desired.version}'
```

RHOAI 3.x requires **OCP 4.19+**. If the cluster is 4.18 or earlier, the maximum supported RHOAI version is **2.25**. See [compatibility reference](reference.md#version-compatibility).

### 1.2 Default storage class

```
oc get storageclass
```

At least one storage class must be marked `(default)`.

### 1.3 Existing installs

Check for existing RHOAI or Open Data Hub installations:

```
oc get csv -A | grep -iE 'rhods|opendatahub'
oc get datasciencecluster -A
```

Open Data Hub **must not** be installed alongside RHOAI. If RHOAI is already installed, confirm the user wants to modify it.

### 1.4 Node capacity

```
oc get nodes --no-headers | wc -l
```

Minimum: 2 worker nodes, 8 CPUs / 32 GiB RAM each.

## Phase 2: Install RHOAI Operator

Use the Kubernetes MCP tools (`resources_create_or_update`) or `oc` CLI. Create these resources **sequentially**:

### 2.1 Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: redhat-ods-operator
```

### 2.2 OperatorGroup

```yaml
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: rhods-operator
  namespace: redhat-ods-operator
```

### 2.3 Subscription

```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: rhods-operator
  namespace: redhat-ods-operator
spec:
  name: rhods-operator
  channel: fast-3.x          # adjust for target version
  source: redhat-operators
  sourceNamespace: openshift-marketplace
```

### 2.4 Wait & verify

Poll until the CSV reaches `Succeeded`:

```
oc get csv -n redhat-ods-operator -l operators.coreos.com/rhods-operator.redhat-ods-operator
```

## Phase 3: Install Prerequisite Operators

Both are required for KServe and distributed workloads (Kueue, Ray, Training Operator).

### 3.1 cert-manager Operator for Red Hat OpenShift

| Resource | Value |
|----------|-------|
| Namespace | `openshift-cert-manager-operator` |
| OperatorGroup | `openshift-cert-manager-operator` (no targetNamespaces — cluster-wide) |
| Package | `openshift-cert-manager-operator` |
| Channel | `stable-v1` |
| Source | `redhat-operators` |

### 3.2 Red Hat build of Kueue (RHBoK)

**Important**: There is no plain `stable` channel. Look up available channels first:

```
oc get packagemanifest kueue-operator -o jsonpath='{.status.defaultChannel}'
```

| Resource | Value |
|----------|-------|
| Namespace | `openshift-kueue-operator` |
| OperatorGroup | `openshift-kueue-operator` (no targetNamespaces — AllNamespaces mode required) |
| Package | `kueue-operator` |
| Channel | use `defaultChannel` from PackageManifest (e.g. `stable-v1.3`) |
| Source | `redhat-operators` |

After the operator is `Succeeded`, create the **Kueue CR** (cluster-scoped, name must be `cluster`):

```yaml
apiVersion: kueue.openshift.io/v1
kind: Kueue
metadata:
  name: cluster
spec:
  managementState: Managed
  config:
    integrations:
      frameworks:
      - BatchJob
```

**Note**: The MCP tool may not recognize newly created CRDs. If `resources_create_or_update` fails with "no matches for kind", use `oc apply` via the Shell tool instead.

## Phase 4: Create DataScienceCluster

Per the distributed workloads docs, set `kueue` to **`Unmanaged`** so the RHBoK operator manages it. Set other components to `Managed` or `Removed` based on user needs.

```yaml
apiVersion: datasciencecluster.opendatahub.io/v2
kind: DataScienceCluster
metadata:
  name: default-dsc
spec:
  components:
    dashboard:
      managementState: Managed
    workbenches:
      managementState: Managed
      workbenchNamespace: rhods-notebooks
    aipipelines:
      argoWorkflowsControllers:
        managementState: Managed    # set Removed only if using own Argo instance
      managementState: Managed
    kserve:
      managementState: Managed
    kueue:
      managementState: Unmanaged    # RHBoK manages Kueue
      defaultClusterQueueName: default
      defaultLocalQueueName: default
    ray:
      managementState: Managed
    trainingoperator:
      managementState: Managed
    # Set remaining to Removed unless specifically needed:
    feastoperator:
      managementState: Removed
    llamastackoperator:
      managementState: Removed
    modelregistry:
      managementState: Removed
      registriesNamespace: rhoai-model-registries
    trustyai:
      managementState: Removed
```

### Verify

Wait for DSC to reach `Ready`:

```
oc get datasciencecluster default-dsc -o jsonpath='{.status.phase}'
```

Check component conditions:

```
oc get datasciencecluster default-dsc \
  -o jsonpath='{range .status.conditions[*]}{.type}: {.status} - {.message}{"\n"}{end}'
```

Common issues:
- **AIPipelines error about missing Argo CRD**: Set `argoWorkflowsControllers.managementState` to `Managed`
- **KServe LLM warnings**: Informational only — requires Connectivity Link Operator for llm-d (OCP 4.20+)

## Phase 5: Configure Users and Groups

Per the [user management docs](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.3/html/managing_openshift_ai/managing-users-and-groups).

### 5.1 Create groups

```bash
oc adm groups new rhods-admins
oc adm groups new rhods-users
```

### 5.2 Add users to groups

```bash
# RHOAI admins — can configure settings, manage all projects
oc adm groups add-users rhods-admins <admin-username>

# Data scientists / regular users — access workbenches, pipelines in own projects
oc adm groups add-users rhods-users <user-username>
```

Users who should have both roles go in both groups.

### 5.3 Configure dashboard access control

```bash
oc patch odhdashboardconfig odh-dashboard-config \
  -n redhat-ods-applications --type=merge \
  -p '{"spec":{"groupsConfig":{"adminGroups":"rhods-admins","allowedGroups":"rhods-users,rhods-admins"}}}'
```

This restricts dashboard access to only users in these groups.

### 5.4 Adding identity provider users

On **ROSA HCP** clusters, the OAuth resource is managed at the hosted control plane level. New users must be added via:
- `rosa create idp` (requires AWS + OCM credentials), or
- [OCM console](https://console.redhat.com/openshift/) → cluster → Access control → Identity providers

On **self-managed OCP** clusters, create an htpasswd secret in `openshift-config` and configure the OAuth resource directly.

**Important**: OpenShift user/identity objects are created on **first login**. Users added to groups before their first login will work — the group membership takes effect when they authenticate.

## Phase 6: Verification Summary

Run this final check:

```bash
echo "=== Operators ==="
oc get csv -n redhat-ods-operator -o custom-columns=NAME:.metadata.name,VERSION:.spec.version,PHASE:.status.phase
echo "=== cert-manager ==="
oc get csv -n openshift-cert-manager-operator -l operators.coreos.com/openshift-cert-manager-operator.openshift-cert-manager-operator -o custom-columns=NAME:.metadata.name,PHASE:.status.phase
echo "=== Kueue ==="
oc get csv -n openshift-kueue-operator -l operators.coreos.com/kueue-operator.openshift-kueue-operator -o custom-columns=NAME:.metadata.name,PHASE:.status.phase
echo "=== DSC ==="
oc get datasciencecluster default-dsc -o jsonpath='Phase: {.status.phase}{"\n"}'
echo "=== Groups ==="
oc get groups
echo "=== Dashboard Config ==="
oc get odhdashboardconfig odh-dashboard-config -n redhat-ods-applications -o jsonpath='{.spec.groupsConfig}'
echo ""
echo "=== Dashboard URL ==="
oc get consolelink rhodslink -o jsonpath='{.spec.href}'
echo ""
```

Present results in a summary table to the user.

## What You Don't Do

- Don't skip the prerequisites check. Version incompatibility wastes significant time.
- Don't use a plain `stable` channel for the Kueue operator — always check `defaultChannel`.
- Don't modify the OAuth resource on ROSA HCP clusters — it will be rejected.
- Don't set `kueue.managementState` to `Managed` when using RHBoK — use `Unmanaged`.
- Don't create the DataScienceCluster before prerequisite operators reach `Succeeded`.
