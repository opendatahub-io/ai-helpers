# Konflux sandbox troubleshooting

Diagnose the earliest failed stage. Do not repeatedly recreate resources or
reinstall the GitHub App without evidence.

## Authentication and discovery

| Symptom | Check | Resolution |
|---|---|---|
| `system:anonymous` or API discovery errors | `oc whoami` and `oc whoami --show-server` | Complete staging login and retry. |
| `oc auth can-i` returns `no` | Identity, server, team-group membership | Refresh authentication; escalate RoleBinding/group synchronization if still denied. |
| Resource type is unknown | `oc api-resources` | Use the API resource/group exposed by the cluster. |

## Component onboarding

Inspect the Component without exposing secrets:

```bash
oc get component <component-name> -n aipcc-sandbox-tenant -o yaml
```

Look for `build.appstudio.openshift.io/status` and the configured source URL,
branch, context, and Containerfile. Then list PaC Repository objects:

```bash
oc get repositories.pipelinesascode.tekton.dev -n aipcc-sandbox-tenant
```

If the Component exists but no Repository exists, verify that Konflux Staging
is installed on the exact GitHub repository and that the organization is
allowed by the staging instance. Resolve the reported Component status before
retrying onboarding.

## Generated pull request is missing

Check:

1. The Component source URL points to the intended repository.
2. The target branch exists.
3. Konflux Staging has repository access and installation approval is complete.
4. Branch protections permit the App to create its setup branch and pull
   request.
5. The Component status reports successful PaC configuration.

Re-request configuration only after fixing the cause:

```bash
oc annotate component <component-name> \
  -n aipcc-sandbox-tenant \
  build.appstudio.openshift.io/request=configure-pac \
  --overwrite
```

This is a mutation and may open another pull request. Confirm before running it.

## No PipelineRun after a GitHub event

Verify in order:

1. `.tekton/` definitions exist on the target branch.
2. The relevant definition matches `pull_request` or `push` and the actual
   target branch.
3. Any path-change expression includes the changed file.
4. The pull request was created after pipeline configuration reached the
   target branch.
5. GitHub shows the Konflux Staging App installed for the repository.
6. An authorized user supplied `/ok-to-test` when PaC requested approval.
7. A PaC Repository object exists in the sandbox tenant.

If onboarding is healthy but a push event was missed, request one build after
confirmation:

```bash
oc annotate component <component-name> \
  -n aipcc-sandbox-tenant \
  build.appstudio.openshift.io/request=trigger-pac-build \
  --overwrite
```

## PipelineRun exists but fails

Inspect the failed task and its logs before changing configuration:

- Clone failure: verify App access, repository URL, and revision.
- Containerfile failure: reproduce or correct the build locally when practical.
- Image push failure: verify the tenant-provided destination and associated
  service account; do not substitute a product registry.
- Quota or scheduling failure: report the PipelineRun and task names to the
  tenant administrators; do not raise quota or broaden privileges automatically.

Retest only after identifying a plausible correction. Avoid unlimited retries;
after two unchanged failures, stop and present the evidence and escalation
target to the engineer.
