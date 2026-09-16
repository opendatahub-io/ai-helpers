# GitHub project onboarding and pipeline run

Use this procedure only after tenant access is verified.

## Collect and validate project inputs

Obtain or discover these values and show them back to the engineer before any
mutation:

| Value | Guidance |
|---|---|
| GitHub identity | Discover with authenticated `gh` or ask for the engineer's handle. |
| GitHub repository | Require an exact `https://github.com/<owner>/<repository>` URL. |
| Visibility | Private and public repositories are supported. |
| Target branch | Discover from GitHub when possible; otherwise ask. |
| Local checkout | Required only when creating or modifying project files. |
| Build context | Default to the repository root only after confirmation. |
| Containerfile | Discover an existing file or ask for the intended path. |
| Application name | Ask the engineer or propose a DNS-compatible name based on their repository. |
| Component name | Ask the engineer or propose a unique DNS-compatible name. |
| Creation interface | Ask whether to use the Konflux UI or `oc`; do not assume one from tool availability. |

Use `gh auth status`, `gh api user --jq .login`, and
`gh repo view <owner/repository>` for read-only discovery when the GitHub CLI
is available. Never output authentication tokens.

The sandbox Applications page is:

<https://konflux-ui.apps.stone-stg-rh01.l2vh.p1.openshiftapps.com/ns/aipcc-sandbox-tenant/applications>

This URL is specific to `aipcc-sandbox-tenant` on Konflux staging. If it is
unavailable, verify the maintained team documentation or ask a Konflux
administrator for the replacement; never redirect the engineer to production.

## Install the GitHub App

The required App is [Konflux Staging](https://github.com/apps/konflux-staging),
with slug `konflux-staging`. If `konflux-staging-internal` is present, select
Konflux Staging for this workflow instead.

For a private repository, the App must be installed with explicit access to
that repository. Guide the engineer to:

1. Open the Konflux Staging App page and choose **Configure**.
2. Select the account or organization that owns the repository.
3. Choose **Only select repositories**.
4. Select the confirmed repository.
5. Review the requested permissions and install the App or request approval.
6. Verify the installation under the repository's GitHub App settings.

Do not install the App for every organization repository unless the engineer
explicitly requests that scope and has authority to approve it. If installation
is pending or the repository is unavailable, stop and ask an organization owner
or repository administrator to approve access.

## Prepare the source repository

For a custom project, verify that the selected build context and Containerfile
exist on the target branch. Preserve the existing implementation.

For a dummy project, use the files under `SKILL_DIR/assets/dummy-project/` only
after checking that the target paths do not exist or after the engineer directs
how to merge them. Let the engineer choose all repository, branch, commit, and
pull-request names.

## Create the Application with the UI

Follow this section only when the engineer selected the Konflux UI. For `oc`,
read [oc-onboarding.md](oc-onboarding.md) instead.

1. Open the sandbox Applications page above and confirm the namespace shown is
   `aipcc-sandbox-tenant`.
2. Open **Applications** and choose **Create application**.
3. Enter the confirmed Application name.
4. Create it and verify it:

   ```bash
   oc get application <application-name> -n aipcc-sandbox-tenant
   ```

Check existing resources before creation. Never reuse or modify another
engineer's Application merely because its name is similar.

## Add the Component with the UI

Open the confirmed Application and choose **Actions → Add component**. Populate
the form with the engineer's values:

- exact HTTPS GitHub repository URL
- target branch
- build context
- Containerfile path relative to the context
- unique Component name
- default pipeline unless the engineer has a specific pipeline requirement
- tenant-provided image destination unless a non-production custom destination
  has been explicitly approved

Create the Component and verify both it and the PaC Repository:

```bash
oc get component <component-name> -n aipcc-sandbox-tenant
oc get repositories.pipelinesascode.tekton.dev -n aipcc-sandbox-tenant
```

## Complete generated pipeline configuration

Konflux normally opens a pull request that adds PipelineRun definitions under
`.tekton/`. Review the exact repository and target branch before merging.

Verify that the target branch contains both pull-request and push definitions,
typically named for the Component. Inspect their event conditions rather than
assuming filenames. The push definition must match the intended target branch
and a push event; the pull-request definition must match a pull request against
that branch.

Do not assume merging the generated configuration pull request proves normal
application changes will trigger. Create a separate test change after the
configuration is on the target branch.

## Trigger and observe pipelines

For the pull-request path:

1. Create a user-selected test branch after confirming the target repository.
2. Make a harmless change in the Component's build context.
3. Commit and push only after confirmation.
4. Open a pull request to the configured target branch.
5. If PaC requires authorization, add `/ok-to-test` from an authorized account.

After the pull-request run succeeds, merge only with the engineer's approval.
The merge should create a push event and a separate post-merge PipelineRun.

Observe runs with:

```bash
oc get pipelineruns.tekton.dev -n aipcc-sandbox-tenant --sort-by=.metadata.creationTimestamp
```

Use the Konflux UI or `tkn pipelinerun logs` when available to inspect task
logs. Record the PipelineRun name, status, source commit, `IMAGE_URL`, and
`IMAGE_DIGEST`; do not expose registry credentials.

## Cleanup

Offer cleanup only for resources created during the current workflow. Resolve
their exact names and confirm before deletion. Delete the Component before its
Application, and verify that no other engineer depends on either resource.
