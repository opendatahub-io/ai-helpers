---
description: Deploy a model to OpenShift using the vLLM Helm chart
argument-hint: <action> [model] [options]
---

## Name
odh-ai-helpers:vllm-deploy

## Synopsis
```
/vllm:deploy install granite-7b     # Install a model deployment
/vllm:deploy upgrade granite-7b     # Upgrade an existing deployment
/vllm:deploy uninstall granite-7b   # Remove a deployment
/vllm:deploy test granite-7b        # Test a deployment
```

## Description
Deploys a model to OpenShift using the vLLM Helm chart from the `rhaiis-midstream-snippets` repository. Supports install, upgrade, uninstall, and test operations.

**Resources:**
- Snippets repo: `git@github.com:neuralmagic/rhaiis-midstream-snippets.git`
- Chart path: `charts/vllm/`
- Deployment configs: `charts/deployments/`

## Implementation

### Step 0: Locate Snippets Repository

1. Check for `rhaiis-midstream-snippets/` as a sibling of the current working directory
2. Check `/tmp/rhaiis-midstream-snippets/`
3. If not found: `git clone --depth 1 git@github.com:neuralmagic/rhaiis-midstream-snippets.git /tmp/rhaiis-midstream-snippets`
4. If found: `git -C <path> pull --ff-only origin main`

Set:
- `SNIPPETS_PATH` = path to the cloned/found repo
- `CHART_PATH` = `${SNIPPETS_PATH}/charts/vllm`
- `DEPLOYMENTS_PATH` = `${SNIPPETS_PATH}/charts/deployments`

### Step 1: Gather Parameters

List available deployment configs:
```bash
ls ${DEPLOYMENTS_PATH}/
```

Ask the user for:
1. **Action** - What operation? (install / upgrade / uninstall / test)
2. **Model** - Which deployment config? (show the files from `deployments/`)
3. **Release name** - Helm release name (suggest a default based on the model name)
4. **Namespace** - OpenShift namespace (default: `arc-runners`)

### Step 2: Check Prerequisites

Verify the environment is ready:

1. **Helm available:**
   ```bash
   helm version --short
   ```

2. **OpenShift CLI available and logged in:**
   ```bash
   oc whoami
   ```

3. **Namespace exists:**
   ```bash
   oc get namespace <NAMESPACE>
   ```
   If it doesn't exist, ask the user if they want to create it:
   ```bash
   oc create namespace <NAMESPACE>
   ```

4. **Service account exists** (`vllm-anyuid-sa`):
   ```bash
   oc get sa vllm-anyuid-sa -n <NAMESPACE>
   ```
   If it doesn't exist, guide the user through creating it:
   ```bash
   oc create sa vllm-anyuid-sa -n <NAMESPACE>
   oc adm policy add-scc-to-user anyuid -z vllm-anyuid-sa -n <NAMESPACE>
   ```

If any prerequisite fails, inform the user and stop.

### Step 3: Execute Helm Operation

Based on the chosen action:

**Install:**
```bash
helm install <RELEASE_NAME> ${CHART_PATH} \
  -n <NAMESPACE> \
  -f ${DEPLOYMENTS_PATH}/<VALUES_FILE>
```

**Upgrade:**
```bash
helm upgrade <RELEASE_NAME> ${CHART_PATH} \
  -n <NAMESPACE> \
  -f ${DEPLOYMENTS_PATH}/<VALUES_FILE>
```

**Uninstall:**
```bash
helm uninstall <RELEASE_NAME> -n <NAMESPACE>
```

**Test:**
```bash
helm test <RELEASE_NAME> -n <NAMESPACE>
```

If the user has no cluster access, offer a dry-run with `helm template` instead:
```bash
helm template <RELEASE_NAME> ${CHART_PATH} \
  -n <NAMESPACE> \
  -f ${DEPLOYMENTS_PATH}/<VALUES_FILE>
```

### Step 4: Monitor and Report

After install or upgrade:

1. **Show deployments and routes:**
   ```bash
   kubectl get deployments,routes -n <NAMESPACE>
   ```

2. **Watch rollout status:**
   ```bash
   kubectl rollout status deployment/<RELEASE_NAME> -n <NAMESPACE>
   ```

3. **Extract endpoint URL:**
   ```bash
   kubectl get route <RELEASE_NAME> -n <NAMESPACE> -o jsonpath='{.status.ingress[0].host}'
   ```

4. **Display endpoint** - Present the full URL (e.g., `https://<host>/v1`) and suggest using `/vllm:test-endpoint` to validate the deployment.

After uninstall, confirm resources are cleaned up:
```bash
kubectl get deployments,routes -n <NAMESPACE> | grep <RELEASE_NAME>
```

## Examples

### Install a model
```bash
/vllm:deploy install granite-7b
```

### Upgrade with new values
```bash
/vllm:deploy upgrade granite-7b
```

### Remove a deployment
```bash
/vllm:deploy uninstall granite-7b
```

## Arguments

- **action** (required): Helm operation to perform
  - Options: `install`, `upgrade`, `uninstall`, `test`

- **[model]** (optional): Deployment config name from `charts/deployments/`
  - If omitted, lists available configs and asks user to choose

- **[options]** (optional): Additional parameters
  - `--namespace <ns>` - Override default namespace
  - `--release <name>` - Override release name

## See Also
- **`/vllm:test-endpoint`** - Test a deployed vLLM endpoint
- **`/vllm:downstream-release-status`** - Check release status
