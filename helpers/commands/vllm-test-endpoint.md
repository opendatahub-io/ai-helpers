---
description: Test a deployed vLLM endpoint with health, model listing, and chat completion queries
argument-hint: "[url]"
---

## Name
odh-ai-helpers:vllm-test-endpoint

## Synopsis
```
/vllm:test-endpoint                              # Auto-discover from OpenShift
/vllm:test-endpoint https://vllm.apps.example.com # Test specific endpoint
```

## Description
Tests a deployed vLLM instance by running health checks, listing available models, and optionally sending a chat completion request. Can auto-discover endpoints from OpenShift routes or accept a URL directly.

## Implementation

### Step 1: Determine Endpoint

Ask the user: **Do you have the endpoint URL, or should I auto-discover it from OpenShift?**

**If user provides a URL:** Use it directly as `ENDPOINT`.

**If auto-discover:**

1. List Helm releases to find vLLM deployments:
   ```bash
   helm list -A --filter vllm
   ```

2. List vLLM routes:
   ```bash
   oc get routes -A | grep vllm
   ```

3. Ask the user to pick a route if multiple exist.

4. Extract the host:
   ```bash
   kubectl get route <ROUTE_NAME> -n <NAMESPACE> -o jsonpath='{.status.ingress[0].host}'
   ```

5. Set `ENDPOINT=https://<host>`

### Step 2: Gather Auth

Ask the user: **Does this endpoint require an API key?**

- If yes, ask for the key and use it as `-H "Authorization: Bearer <API_KEY>"` in all requests.
- If no, proceed without auth headers.

### Step 3: Run Checks

#### 3a: Health Check

```bash
curl -s -o /dev/null -w "%{http_code}" ${ENDPOINT}/health
```

Report: healthy (200) or unhealthy (non-200).

#### 3b: Model Listing

```bash
curl -s ${ENDPOINT}/v1/models ${AUTH_HEADER}
```

Report: list of available model IDs.

#### 3c: Chat Completion (optional)

Ask the user if they want to run a test completion. If yes, pick the first model from 3b and send:

```bash
curl -s ${ENDPOINT}/v1/chat/completions ${AUTH_HEADER} \
  -H "Content-Type: application/json" \
  -d '{
    "model": "<MODEL_ID>",
    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
    "max_tokens": 50
  }'
```

### Step 4: Report

Present a summary:

| Check | Result |
|-------|--------|
| Health (`/health`) | `<status>` |
| Models (`/v1/models`) | `<model list>` |
| Chat completion | `<response or skipped>` |

If any check failed, suggest troubleshooting steps:
- Health failed: check pod status with `oc describe pod` or `kubectl get events -n <NAMESPACE>`
- Models failed: the model may still be loading, check logs
- Completion failed: verify the model name matches what `/v1/models` returned

## Examples

### Test a known endpoint
```bash
/vllm:test-endpoint https://vllm-granite.apps.mycluster.example.com
```

### Auto-discover from cluster
```bash
/vllm:test-endpoint
```

## Arguments

- **[url]** (optional): Full URL of the vLLM endpoint
  - If omitted: Auto-discovers from OpenShift routes
  - Example: `https://vllm.apps.example.com`

## See Also
- **`/vllm:deploy`** - Deploy a vLLM model to OpenShift
- **`/vllm:downstream-release-status`** - Check release status
