---
name: module-scaffold
description: >-
  Given a component name, generate a complete standalone ODH module operator
  repository. Produces Go module, CRD types implementing PlatformObject,
  controller skeleton with reconciler builder pattern, Helm chart, Makefile,
  CI config, singleton webhook, and AGENTS.md. Use when starting a new module
  from scratch.
allowed-tools: Bash Read Grep Glob Write Edit
user-invocable: true
argument-hint: "<component-name>"
metadata:
  author: ODH
  version: "1.0"
  tags: "odh, module, scaffold, operator, generator"
---

# ODH Module Scaffold

Generate a complete standalone module operator repository for the ODH platform.

## Step 1: Parse arguments

Extract the component name from `$ARGUMENTS`. If not provided, ask the user.

Derive these values from the component name (example: `model-registry`):

| Variable | Example Value |
|----------|---------------|
| `COMPONENT` | `model-registry` |
| `COMPONENT_SNAKE` | `model_registry` |
| `COMPONENT_PASCAL` | `ModelRegistry` |
| `COMPONENT_LOWER` | `modelregistry` |
| `COMPONENT_LOWER_PLURAL` | `modelregistries` |
| `MODULE_REPO` | `<COMPONENT>-operator` |
| `API_GROUP` | `components.platform.opendatahub.io` |
| `API_VERSION` | `v1alpha1` |
| `SINGLETON_NAME` | `default-<COMPONENT>` |

Ask the user:
1. Which API group to use: `components.platform.opendatahub.io` or
   `services.platform.opendatahub.io`? Default: `components`.
2. Target directory? Default: `./<MODULE_REPO>`.

## Step 2: Create directory structure

Generate this layout:

```text
<MODULE_REPO>/
├── api/<API_VERSION>/
│   ├── <COMPONENT_SNAKE>_types.go
│   ├── <COMPONENT_SNAKE>_common.go
│   ├── groupversion_info.go
│   └── doc.go
├── internal/
│   ├── controller/
│   │   ├── <COMPONENT_SNAKE>_controller.go
│   │   └── <COMPONENT_SNAKE>_controller_actions.go
│   └── webhook/
│       └── singleton.go
├── charts/<MODULE_REPO>/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── serviceaccount.yaml
│       ├── clusterrole.yaml
│       ├── clusterrolebinding.yaml
│       └── _helpers.tpl
├── cmd/
│   └── main.go
├── config/
│   └── samples/
│       └── <COMPONENT_SNAKE>.yaml
├── go.mod
├── Makefile
├── Containerfile
├── .github/workflows/
│   └── ci.yaml
├── .rules/
│   ├── api-types.md
│   ├── controller.md
│   ├── helm-chart.md
│   ├── security.md
│   └── testing.md
├── AGENTS.md
├── README.md
└── .gitignore
```

## Step 3: Generate CRD types

Use the templates from `${CLAUDE_SKILL_DIR}/references/templates.md` to
generate each file. Key requirements:

### `api/<API_VERSION>/<COMPONENT_SNAKE>_types.go`

The CR type must:
- Embed `metav1.TypeMeta` and `metav1.ObjectMeta`
- Have `Spec` field using `<COMPONENT_PASCAL>Spec`
- Have `Status` field using `<COMPONENT_PASCAL>Status`
- Include kubebuilder markers: `+kubebuilder:object:root=true`,
  `+kubebuilder:subresource:status`, `+kubebuilder:resource:scope=Cluster`
- Include CEL singleton validation for the name
- Include compile-time assertion: `var _ common.PlatformObject = (*<COMPONENT_PASCAL>)(nil)`
- Implement all PlatformObject methods (GetStatus, GetConditions,
  SetConditions, GetReleaseStatus, SetReleaseStatus)

The status struct must embed `common.Status` and
`common.ComponentReleaseStatus` inline.

### `api/<API_VERSION>/<COMPONENT_SNAKE>_common.go`

Define `<COMPONENT_PASCAL>CommonSpec` with `common.ManagementSpec` embedded
inline. This struct is inlined into `<COMPONENT_PASCAL>Spec`.

### `api/<API_VERSION>/groupversion_info.go`

Standard kubebuilder groupversion registration using the chosen API group
and version.

### `api/<API_VERSION>/doc.go`

Package doc comment with `+groupName=<API_GROUP>` marker.

## Step 4: Generate controller

### `internal/controller/<COMPONENT_SNAKE>_controller.go`

The controller setup must:
- Use `reconciler.NewReconciler` with functional options pattern
- Register render, deploy, and gc actions (gc MUST be last)
- Configure conditions via `WithConditionsManagerFactory` with Ready as the
  happy condition and ProvisioningSucceeded + Degraded as dependents
- Import from `odh-platform-utilities` packages:
  - `framework/controller/reconciler` for reconciler setup
  - `framework/controller/conditions` for condition management
  - `framework/controller/actions/deploy` for resource deployment
  - `framework/controller/actions/gc` for garbage collection
  - `framework/controller/actions/render` for manifest rendering
  - `framework/api` for Release type
  - `pkg/cluster` for platform detection
  - `pkg/metadata` for label/annotation constants

### `internal/controller/<COMPONENT_SNAKE>_controller_actions.go`

Define three action functions:
1. **renderAction** -- use `framework/controller/actions/render`
2. **deployAction** -- use `framework/controller/actions/deploy` with SSA mode
3. **gcAction** -- use `framework/controller/actions/gc`

Each action follows the signature:
`func(ctx context.Context, rr *types.ReconciliationRequest) error`

## Step 5: Generate Helm chart

### `charts/<MODULE_REPO>/Chart.yaml`

```yaml
apiVersion: v2
name: <MODULE_REPO>
description: Helm chart for the <COMPONENT_PASCAL> module controller
version: 0.1.0
appVersion: "0.1.0"
type: application
```

### `charts/<MODULE_REPO>/values.yaml`

Provide defaults for: image repository/tag, replicas (1), resources
(requests: 100m CPU, 128Mi memory; limits: 500m CPU, 512Mi memory),
service account name, node selector, tolerations.

### Templates

Generate ONLY controller infrastructure manifests:
- **deployment.yaml** -- Controller Deployment with leader election,
  health/readiness probes, security context (non-root, read-only rootfs)
- **serviceaccount.yaml** -- ServiceAccount for the controller
- **clusterrole.yaml** -- ClusterRole with module-specific RBAC (no wildcards)
- **clusterrolebinding.yaml** -- Bind the ClusterRole to the ServiceAccount
- **_helpers.tpl** -- Standard Helm helpers (name, labels, selectors)

Do NOT generate application-level manifests.

## Step 6: Generate supporting files

### `cmd/main.go`

Standard controller-runtime manager setup with:
- Scheme registration for the module API
- Health/readiness endpoints
- Leader election support
- Controller and webhook registration

### `Makefile`

Include targets: `build`, `test`, `lint`, `manifests`, `generate`, `fmt`,
`vet`, `docker-build`, `docker-push`, `helm-lint`.

### `Containerfile`

Multi-stage build: Go builder stage + distroless runtime stage.

### `.github/workflows/ci.yaml`

GitHub Actions workflow with: lint, test, build jobs. Pin actions to full
commit SHAs. Set `permissions: read-all`.

### `AGENTS.md`

Use the comprehensive template from
`${CLAUDE_SKILL_DIR}/../module-compliance/references/agents-md-template.md`
as a starting point. Replace `<COMPONENT_PASCAL>` and other placeholders with
the actual component values. This file provides passive guidance to AI agents
working in the module repo -- covering PlatformObject contract, controller
patterns, Helm chart rules, security, and separation of concerns.

### `.rules/` directory

Copy the rule files from
`${CLAUDE_SKILL_DIR}/../module-compliance/references/rules/` into the
generated repo's `.rules/` directory. These are path-scoped rules that
fire automatically when agents edit matching files (e.g., `api/**/*.go`,
`internal/controller/**/*.go`, `charts/**`). Files to copy:

- `api-types.md` -- CRD type conventions
- `controller.md` -- Controller patterns and GC ordering
- `helm-chart.md` -- Chart content restrictions
- `security.md` -- Webhook, TLS, RBAC, and metadata rules
- `testing.md` -- Test patterns and conventions

### `config/samples/<COMPONENT_SNAKE>.yaml`

A sample CR manifest with the singleton name and `managementState: Managed`.

### `README.md`

Brief README with: project description, prerequisites (Go 1.25+,
controller-runtime, cert-manager), build instructions, usage instructions.

### `.gitignore`

Standard Go gitignore (bin/, vendor/, *.exe, etc.).

## Step 7: Initialize Go module

Run the following commands in the generated directory:

```bash
cd <MODULE_REPO>
go mod init github.com/opendatahub-io/<MODULE_REPO>
go mod edit -require github.com/opendatahub-io/odh-platform-utilities@v0.1.0
```

Note: `go mod tidy` will fail until the controller code compiles. Inform the
user that they should run `go mod tidy` after filling in the controller
implementation details and installing `controller-gen`.

## Step 8: Validate

Suggest the user run the `module-compliance` skill against the generated repo
to verify all contract rules pass. Also suggest running `make lint` and
`make test` once the Go dependencies are resolved.

## Gotchas

- `go mod tidy` will fail until controller-gen generates deepcopy methods and
  all placeholder code compiles. Run `make generate` first.
- The Helm chart must contain ONLY controller manifests. Application workloads
  are embedded in the controller binary and applied by the controller at
  runtime.
- Do not import `github.com/openshift/api` for ManagementState. The shared
  library uses a plain string type that is wire-compatible.
- The GC action must always be the last `.WithAction()` in the reconciler
  builder chain. Deploy stamps annotations that GC reads -- reversing the
  order deletes resources that were just deployed.
- The singleton name in the CEL rule must exactly match what the orchestrator
  creates. Convention is `default-<component>`.
