# AIPCC sandbox access and provisioning

Use this procedure before creating an Application or Component. It covers both
the normal post-provisioning login and the source-controlled access workflow
when the tenant or its maintainer binding is not yet available.

## Fixed sandbox scope

This skill targets the following non-production environment:

| Item | Value |
|---|---|
| GitLab source of truth | `https://gitlab.cee.redhat.com/releng/konflux-release-data` |
| Cluster | `stone-stg-rh01` |
| API server | `https://api.stone-stg-rh01.l2vh.p1.openshiftapps.com:6443` |
| Namespace | `aipcc-sandbox-tenant` |
| Maintainer group | `aipcc-ecosystems` |
| Maintainer ClusterRole | `konflux-maintainer-user-actions` |

Do not substitute a production cluster, tenant, or release-data path. The
engineer's GitLab handle, branch name, change title, reviewers, and any additional
tenant administrators must be provided or discovered at runtime.

## Required inputs

The skill is specifically for the `aipcc-sandbox-tenant` namespace and the
`aipcc-ecosystems` team. Obtain the current Konflux staging API server from the
engineer, their existing `oc` context, or maintained team documentation. Do not
guess an endpoint or reuse a production endpoint.

Do not ask for a token. Authentication must happen through the engineer's own
browser or approved local credential flow.

## Verify tools and identity

Check whether `oc` is available. If the engineer is not authenticated, guide
them through the current staging login command using the API server they
confirmed:

```bash
oc login --web <staging-api-server>
```

For this skill's sandbox, the confirmed staging endpoint is:

```text
https://api.stone-stg-rh01.l2vh.p1.openshiftapps.com:6443
```

Verify the resulting session:

```bash
oc whoami
oc whoami --show-server
oc config current-context
```

Stop if `oc whoami` fails or reports `system:anonymous`. Confirm that the server
is staging before continuing.

## Verify effective tenant access

Switch to the tenant and test permissions against namespaced Konflux resources:

```bash
oc project aipcc-sandbox-tenant
oc auth can-i create applications.appstudio.redhat.com -n aipcc-sandbox-tenant
oc auth can-i create components.appstudio.redhat.com -n aipcc-sandbox-tenant
oc auth can-i get pipelineruns.tekton.dev -n aipcc-sandbox-tenant
```

API groups may evolve. If discovery says a resource type is unknown, run
`oc api-resources` and substitute the resource name/group exposed by that
cluster. Do not interpret an unknown resource warning as a valid RBAC result.

Test maintainer access with the namespaced resource checks above. Namespace
objects are cluster-scoped and may be hidden even when namespaced access is
valid, so `oc get namespace` is not conclusive.

## Request or provision access through `konflux-release-data`

Use this section only when the tenant is absent, its source configuration lacks
the `aipcc-ecosystems` maintainer binding, or an authorized administrator asks
for a configuration change. The repository is the source of truth; never use
`oc apply` to create or patch the namespace or its RBAC.

### Check repository authority

The engineer needs permission to push a branch and submit a GitLab change in
`releng/konflux-release-data`. Check credentials without printing tokens:

```bash
glab auth status --hostname gitlab.cee.redhat.com
```

If `glab` is unavailable or access is denied, use the GitLab web UI or ask
Releng to add the engineer's approved GitLab group to
`konflux-release-data-users`. Do not fork this repository: its CI depends on
repository configuration that forks do not receive.

### Update an existing tenant's maintainer binding

Clone the repository or use an existing clean checkout, then create a
user-selected branch from `main`:

```bash
git clone --single-branch --branch main git@gitlab.cee.redhat.com:releng/konflux-release-data.git
cd konflux-release-data
git switch --create <user-selected-branch>
```

Inspect the source files for this tenant:

```text
staging/tenants-config/cluster/stone-stg-rh01/tenants/aipcc-sandbox-tenant/kustomization.yaml
staging/tenants-config/cluster/stone-stg-rh01/tenants/aipcc-sandbox-tenant/rbac-maintainers.yaml
```

If `rbac-maintainers.yaml` lacks the team binding, add the following subject
to the existing RoleBinding. Preserve the existing role reference and do not
replace approved administrators:

```yaml
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: Group
    name: aipcc-ecosystems
```

Do not edit files under `staging/tenants-config/auto-generated/` by hand. From
`staging/tenants-config`, regenerate only this tenant's derived manifests:

```bash
./build-single.sh aipcc-sandbox-tenant
```

Review the source and generated diff, then run the repository's normal checks:

```bash
git diff --check
git diff -- staging/tenants-config/cluster/stone-stg-rh01/tenants/aipcc-sandbox-tenant staging/tenants-config/auto-generated/cluster/stone-stg-rh01/tenants/aipcc-sandbox-tenant
```

The generated output should contain the same group subject under the tenant's
maintainer RoleBinding. Do not commit unrelated generated changes.

Commit only the reviewed source and generated files:

```bash
git add staging/tenants-config/cluster/stone-stg-rh01/tenants/aipcc-sandbox-tenant/rbac-maintainers.yaml staging/tenants-config/auto-generated/cluster/stone-stg-rh01/tenants/aipcc-sandbox-tenant
git diff --cached --check
git commit -m "Grant AIPCC ecosystems maintainer access"
```

Immediately before pushing or submitting the change, confirm the branch,
tenant path, group subject, and staged file list. Push and open the change only
with the engineer's approval:

```bash
git push --set-upstream origin <user-selected-branch>
glab mr create --repo https://gitlab.cee.redhat.com/releng/konflux-release-data --source-branch <user-selected-branch> --target-branch main --title "<user-selected-title>" --description "Grant the aipcc-ecosystems group maintainer access to aipcc-sandbox-tenant on stone-stg-rh01."
```

The GitLab web UI is an equivalent option. With the CLI, use `glab mr create`
without `--fill` or `--push` because the branch push and change submission are
separate confirmed mutations.

### Create a new tenant only with explicit authority

If the tenant directory is absent, stop and determine whether the engineer is
authorized to provision a shared tenant. Creating a new namespace requires
confirmed administrators, codeowners, quota tier, and reviewers. Use the
repository's current `add-namespace.sh` help and documentation rather than
copying a historical change:

```bash
cd staging/tenants-config
./add-namespace.sh --help
```

Do not create a second tenant for an individual engineer when the shared
`aipcc-sandbox-tenant` is the intended target. If authority or required
administrator/codeowner values are missing, prepare an access request instead.

### Submit and merge the change

After the engineer reviews the exact diff, confirm the target repository,
branch, tenant path, and group subject immediately before pushing or submitting
the change. Push the user-selected branch directly to the repository
when authorized; otherwise use the GitLab UI or ask an authorized maintainer.

The change must pass repository CI and receive the approvals required
by the current CODEOWNERS entries. Do not merge it merely because the generated
YAML looks correct. If the engineer cannot merge, identify the current
CODEOWNERS approval path without inventing reviewer identities.

### Wait for reconciliation and refresh access

After the change merges, wait for the release-data pipeline and ArgoCD
tenant synchronization to complete. Then refresh the engineer's cluster
session so new group claims are included:

```bash
oc logout
oc login --web https://api.stone-stg-rh01.l2vh.p1.openshiftapps.com:6443
```

Repeat the effective permission checks. Do not continue to Application or
Component creation until they return the required permissions.

## When access is denied

1. Confirm that the engineer belongs to the `aipcc-ecosystems` access group.
2. Log out and reauthenticate to refresh group claims:

   ```bash
   oc logout
   oc login --web <staging-api-server>
   ```

3. Repeat the namespaced `oc auth can-i` checks.
4. If access is still denied, prepare a support request containing only:
   - `oc whoami` output
   - `oc whoami --show-server` output
   - tenant name
   - denied `oc auth can-i` commands and results
   - confirmation of team-group membership
   - release-data change URL and merge/reconciliation status, if a change was used

Ask a tenant administrator or the Konflux support channel to verify that the
tenant RoleBinding is synchronized and that the authenticated identity contains
the expected group. Do not ask the engineer to share their token or kubeconfig.

Continue only after the namespaced Application, Component, and PipelineRun
checks show the permissions needed for the selected workflow.
