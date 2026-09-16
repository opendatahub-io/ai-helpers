---
name: konflux-sandbox-onboarding
description: Guide AIPCC engineers through obtaining access to the shared Konflux sandbox, onboarding a user-selected GitHub repository or dummy project, and verifying pull-request and push pipelines. Use when an engineer wants a hands-on Konflux staging experiment; exclude production tenants and release configuration.
---

# Konflux Sandbox Onboarding

Guide the engineer from access verification to one successful build while
keeping every user- and project-specific value configurable.

## Constraints

- Work only in the AIPCC sandbox tenant on Konflux staging.
- Use sandbox-scoped repositories, credentials, and image destinations; if a
  supplied target is production, stop and ask for a non-production substitute.
- Never invent or retain an engineer's identity, GitHub handle, organization,
  repository, branch, local path, Application name, or Component name.
- Discover values from authenticated tools when practical; otherwise ask for
  only the missing values. Confirm inferred values before mutations.
- Never request, print, persist, or quote access tokens, kubeconfig contents,
  secret values, or GitHub App private data.
- Use **Konflux Staging** (`konflux-staging`), not **Konflux Staging Internal**.
- Use the [AIPCC sandbox Applications
  page](https://konflux-ui.apps.stone-stg-rh01.l2vh.p1.openshiftapps.com/ns/aipcc-sandbox-tenant/applications)
  for the UI workflow. Do not substitute a production console or guess a new
  endpoint if this staging URL is unavailable.
- Treat `konflux-release-data` as the source of truth for tenant provisioning
  and RBAC. Do not apply tenant or RoleBinding manifests directly to the
  cluster.
- Scope GitHub App installation to selected repositories. Do not propose
  organization-wide installation unless the engineer explicitly requests it
  and has authority to approve it.
- Preserve existing repository files. Before copying the dummy project, inspect
  the target and stop if a file would be overwritten.
- Treat installing an App, editing or pushing `konflux-release-data`, opening
  or merging a GitLab change, creating cluster resources, pushing a branch,
  opening or merging a pull request, triggering a build, and deleting resources
  as mutations. Confirm the intended target immediately before performing them.

## Workflow routing

1. Resolve the directory containing this `SKILL.md` as `SKILL_DIR` and use its
   resources through paths derived from that directory.
2. Determine whether the engineer needs access setup, project onboarding,
   pipeline execution, troubleshooting, or the full workflow. Resume at their
   current phase instead of repeating completed steps.
3. Read [references/access.md](references/access.md) when access is not yet
   verified. If the tenant or maintainer binding is missing, use its
   release-data change workflow or produce an access request before attempting
   project creation. Proceed only after the effective permission checks pass.

## Project inputs

Collect or discover:

- GitHub identity from authenticated `gh`, when available
- exact repository URL, visibility, and target branch, or a request for a dummy
  repository
- local checkout, build context, and Containerfile path
- Application and Component names, or permission to propose them
- creation interface: Konflux UI or `oc`
- pipeline and image visibility when sandbox defaults are unsuitable

## Project and pipeline workflow

1. For dummy mode, inspect `SKILL_DIR/assets/dummy-project/`, explain which
   files will be copied, inspect the target repository, and obtain confirmation
   before copying. Never initialize, overwrite, commit, or push without the
   engineer's approval.
2. Read [references/github-onboarding.md](references/github-onboarding.md), then
   prepare the repository and GitHub App access using the collected values.
3. Follow the UI sections in
   [references/github-onboarding.md](references/github-onboarding.md) when the
   engineer chooses the Konflux UI. When they choose `oc`, read
   [references/oc-onboarding.md](references/oc-onboarding.md) and follow its
   manifest validation, creation, and verification procedure. Fill every
   placeholder with a confirmed value before presenting or running a command.
4. Distinguish the Konflux-generated `.tekton/` configuration pull request from
   the later test pull request. Verify the configuration is on the target branch
   before expecting ordinary pull-request or push pipelines.
5. Observe the run in GitHub, the Konflux UI, or with `oc`. Capture only
   non-secret evidence: resource names, commit SHA, PipelineRun name, status,
   image URL/digest, and relevant error messages.
6. If a step fails, read
   [references/troubleshooting.md](references/troubleshooting.md) and diagnose
   the earliest broken link in the chain: authentication, tenant RBAC, GitHub
   App access, Component onboarding, PaC Repository creation, event matching,
   PipelineRun creation, or build execution.
7. Finish with a concise progress summary: completed phases, resources created,
    latest run result, remaining action, and safe cleanup commands. Never delete
    shared or unverified resources.

## Dummy project asset

Use both files in [assets/dummy-project/](assets/dummy-project/) only when the
engineer chooses dummy mode. The Containerfile accepts build arguments so the
engineer can customize the displayed owner and message without editing the
pipeline definition.

## Error handling

| Condition | Action |
|---|---|
| `oc` reports `system:anonymous` | Stop and complete staging authentication. |
| Tenant permission checks return `no` | Stop project setup and follow the access escalation procedure. |
| Tenant or maintainer binding is missing | Follow the `konflux-release-data` change workflow in [references/access.md](references/access.md); do not apply RBAC directly. |
| GitLab push or contribution permission is missing | Stop and request membership in the approved release-data access group or ask a tenant administrator to open the change. |
| GitHub repository or App target is ambiguous | Ask for the exact `owner/repository`; defer installation and pushes. |
| Existing files conflict with dummy assets | Stop and offer a different directory or user-directed merge. |
| `oc apply --dry-run=server` rejects a manifest | Do not create the resource; inspect the live CRD and correct the manifest. |
| Generated configuration pull request is missing | Inspect Component status, App installation, and PaC Repository before retrying. |
| No PipelineRun follows an event | Verify `.tekton/`, target branch, event expressions, and `/ok-to-test`. |
| A command would affect production or another engineer's resources | Refuse that target and return to the sandbox scope. |
