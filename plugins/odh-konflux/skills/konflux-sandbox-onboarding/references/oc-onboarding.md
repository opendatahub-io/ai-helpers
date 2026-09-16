# Create Konflux resources with `oc`

Use this procedure only after tenant access, the GitHub repository, and
Konflux Staging App access are verified. It is the CLI alternative to creating
the Application and Component in the Konflux UI.

## Confirm inputs and API support

Confirm every value before generating manifests:

- Application and Component names
- exact HTTPS GitHub repository URL
- target branch, build context, and Containerfile path
- build pipeline name
- image visibility

For a Containerfile build, propose `docker-build-oci-ta` as the staging default
and `private` image visibility, but let the engineer choose different
non-production values. Component names must be unique across the namespace.

Verify the live API and permissions instead of assuming a CRD version:

```bash
oc api-resources --api-group=appstudio.redhat.com
oc auth can-i create applications.appstudio.redhat.com -n aipcc-sandbox-tenant
oc auth can-i create components.appstudio.redhat.com -n aipcc-sandbox-tenant
oc auth can-i create imagerepositories.appstudio.redhat.com -n aipcc-sandbox-tenant
```

The examples below use the `appstudio.redhat.com/v1alpha1` version currently
exposed by Konflux staging. If discovery reports a different version, inspect
it with `oc explain` and adapt the manifests before continuing.

## Check for conflicts

Check all three names before creating anything:

```bash
oc get application <application-name> -n aipcc-sandbox-tenant --ignore-not-found
oc get component <component-name> -n aipcc-sandbox-tenant --ignore-not-found
oc get imagerepository <component-name> -n aipcc-sandbox-tenant --ignore-not-found
```

Stop if any command returns a resource. Do not adopt, patch, or delete an
existing resource without establishing ownership and receiving explicit
approval.

## Generate the Application manifest

Create `Application.yaml` in a location approved by the engineer:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Application
metadata:
  name: <application-name>
  namespace: aipcc-sandbox-tenant
spec:
  displayName: <application-name>
```

Replace both name placeholders with the confirmed Application name. Validate
against the live API, show the final manifest or diff to the engineer, and
confirm the target immediately before applying it:

```bash
oc apply --dry-run=server -f Application.yaml
oc apply -f Application.yaml
oc get application <application-name> -n aipcc-sandbox-tenant
```

Do not run the non-dry-run command until the engineer confirms creation.

## Generate the Component and image manifests

Create `Component.yaml` using the confirmed values:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: Component
metadata:
  name: <component-name>
  namespace: aipcc-sandbox-tenant
  annotations:
    build.appstudio.openshift.io/request: configure-pac
    build.appstudio.openshift.io/pipeline: '{"name":"<pipeline-name>","bundle":"latest"}'
    git-provider: github
    git-provider-url: https://github.com
spec:
  application: <application-name>
  componentName: <component-name>
  source:
    git:
      url: https://github.com/<owner>/<repository>
      revision: <target-branch>
      context: <build-context>
      dockerfileUrl: <containerfile-path>
```

Create `ImageRepository.yaml` to request a sandbox image repository and let the
image controller update the Component's `spec.containerImage`:

```yaml
apiVersion: appstudio.redhat.com/v1alpha1
kind: ImageRepository
metadata:
  name: <component-name>
  namespace: aipcc-sandbox-tenant
  annotations:
    image-controller.appstudio.redhat.com/update-component-image: "true"
  labels:
    appstudio.redhat.com/application: <application-name>
    appstudio.redhat.com/component: <component-name>
spec:
  image:
    name: aipcc-sandbox-tenant/<component-name>
    visibility: <public-or-private>
```

The Containerfile path is relative to the build context. Replace every
placeholder and reject any manifest that still contains angle-bracket values.
Do not add `spec.containerImage` when using this ImageRepository flow.

Validate both resources before creation:

```bash
oc apply --dry-run=server -f Component.yaml
oc apply --dry-run=server -f ImageRepository.yaml
```

Show the final manifests or diff, confirm the repository and resource names,
then obtain approval immediately before applying them:

```bash
oc apply -f Component.yaml
oc apply -f ImageRepository.yaml
```

## Verify onboarding

Wait for the image controller and build service to reconcile, then inspect only
non-secret fields:

```bash
oc get application <application-name> -n aipcc-sandbox-tenant
oc get component <component-name> -n aipcc-sandbox-tenant
oc get imagerepository <component-name> -n aipcc-sandbox-tenant
oc get component <component-name> -n aipcc-sandbox-tenant \
  -o jsonpath='{.spec.containerImage}{"\n"}'
oc get repositories.pipelinesascode.tekton.dev -n aipcc-sandbox-tenant
```

Inspect the Component status if `spec.containerImage` remains empty or no PaC
Repository appears. Do not recreate resources while controllers are still
reconciling.

The `configure-pac` request should open the generated `.tekton/` configuration
pull request. Return to [github-onboarding.md](github-onboarding.md) to review
that pull request and run separate pull-request and push pipeline tests.

For the upstream resource examples, see [Creating applications and
components](https://konflux-ci.dev/docs/building/creating/) and [Onboarding a
component from GitHub](https://konflux-ci.dev/docs/building/creating-github/).
