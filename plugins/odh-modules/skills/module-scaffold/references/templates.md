# Module Scaffold Templates

Code templates for generating ODH module operator repositories. Replace
placeholders (`<COMPONENT_PASCAL>`, `<COMPONENT_SNAKE>`, `<API_GROUP>`,
`<API_VERSION>`, `<MODULE_REPO>`, `<SINGLETON_NAME>`, `<COMPONENT_LOWER_PLURAL>`)
with actual values.

---

## CRD Types (`api/<API_VERSION>/<COMPONENT_SNAKE>_types.go`)

```go
package <API_VERSION>

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/opendatahub-io/odh-platform-utilities/api/common"
)

// <COMPONENT_PASCAL>Spec defines the desired state of <COMPONENT_PASCAL>.
type <COMPONENT_PASCAL>Spec struct {
	<COMPONENT_PASCAL>CommonSpec `json:",inline"`
}

// <COMPONENT_PASCAL>Status defines the observed state of <COMPONENT_PASCAL>.
type <COMPONENT_PASCAL>Status struct {
	common.Status                 `json:",inline"`
	common.ComponentReleaseStatus `json:",inline"`
}

// +kubebuilder:object:root=true
// +kubebuilder:subresource:status
// +kubebuilder:resource:scope=Cluster
// +kubebuilder:printcolumn:name="Ready",type=string,JSONPath=`.status.phase`
// +kubebuilder:validation:XValidation:rule="self.metadata.name == '<SINGLETON_NAME>'",message="<COMPONENT_PASCAL> name must be <SINGLETON_NAME>"
type <COMPONENT_PASCAL> struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`

	Spec   <COMPONENT_PASCAL>Spec   `json:"spec,omitempty"`
	Status <COMPONENT_PASCAL>Status `json:"status,omitempty"`
}

// +kubebuilder:object:root=true
type <COMPONENT_PASCAL>List struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitempty"`
	Items           []<COMPONENT_PASCAL> `json:"items"`
}

func init() {
	SchemeBuilder.Register(&<COMPONENT_PASCAL>{}, &<COMPONENT_PASCAL>List{})
}

// --- PlatformObject implementation ---

func (c *<COMPONENT_PASCAL>) GetStatus() *common.Status {
	return &c.Status.Status
}

func (c *<COMPONENT_PASCAL>) GetConditions() []common.Condition {
	return c.Status.Conditions
}

func (c *<COMPONENT_PASCAL>) SetConditions(conditions []common.Condition) {
	c.Status.Conditions = conditions
}

func (c *<COMPONENT_PASCAL>) GetReleaseStatus() *common.ComponentReleaseStatus {
	return &c.Status.ComponentReleaseStatus
}

func (c *<COMPONENT_PASCAL>) SetReleaseStatus(status common.ComponentReleaseStatus) {
	c.Status.ComponentReleaseStatus = status
}

var _ common.PlatformObject = (*<COMPONENT_PASCAL>)(nil)
```

---

## CommonSpec (`api/<API_VERSION>/<COMPONENT_SNAKE>_common.go`)

```go
package <API_VERSION>

import (
	"github.com/opendatahub-io/odh-platform-utilities/api/common"
)

// <COMPONENT_PASCAL>CommonSpec defines user-facing configuration shared between
// the module CR and the DSC stanza.
type <COMPONENT_PASCAL>CommonSpec struct {
	common.ManagementSpec `json:",inline"`
}
```

---

## GroupVersion (`api/<API_VERSION>/groupversion_info.go`)

```go
package <API_VERSION>

import (
	"k8s.io/apimachinery/pkg/runtime/schema"
	"sigs.k8s.io/controller-runtime/pkg/scheme"
)

var (
	GroupVersion = schema.GroupVersion{
		Group:   "<API_GROUP>",
		Version: "<API_VERSION>",
	}

	SchemeBuilder = &scheme.Builder{GroupVersion: GroupVersion}

	AddToScheme = SchemeBuilder.AddToScheme
)
```

---

## Doc (`api/<API_VERSION>/doc.go`)

```go
// +groupName=<API_GROUP>
package <API_VERSION>
```

---

## Controller (`internal/controller/<COMPONENT_SNAKE>_controller.go`)

```go
package controller

import (
	"context"

	"sigs.k8s.io/controller-runtime/pkg/manager"

	<API_VERSION> "github.com/opendatahub-io/<MODULE_REPO>/api/<API_VERSION>"
	fwapi "github.com/opendatahub-io/odh-platform-utilities/framework/api"
	"github.com/opendatahub-io/odh-platform-utilities/framework/controller/reconciler"
)

func SetupController(ctx context.Context, mgr manager.Manager) error {
	_, err := reconciler.ReconcilerFor(mgr, &<API_VERSION>.<COMPONENT_PASCAL>{}).
		WithInstanceName("<COMPONENT>").
		WithReconcilerOpts(reconciler.WithRelease(fwapi.Release{})).
		WithDynamicOwnership().
		WithAction(renderAction).
		WithAction(deployAction).
		WithAction(gcAction).
		Build(ctx)

	return err
}
```

---

## Controller Actions (`internal/controller/<COMPONENT_SNAKE>_controller_actions.go`)

```go
package controller

import (
	"context"

	"github.com/opendatahub-io/odh-platform-utilities/framework/controller/actions/deploy"
	"github.com/opendatahub-io/odh-platform-utilities/framework/controller/actions/gc"
	"github.com/opendatahub-io/odh-platform-utilities/framework/controller/actions/render/helm"
	"github.com/opendatahub-io/odh-platform-utilities/framework/controller/types"
)

func renderAction(ctx context.Context, rr *types.ReconciliationRequest) error {
	// TODO: implement — use helm.NewAction to render manifests from embedded chart
	_ = helm.NewAction
	return nil
}

func deployAction(ctx context.Context, rr *types.ReconciliationRequest) error {
	// TODO: implement — use deploy.NewAction to apply rendered resources via SSA
	_ = deploy.NewAction
	return nil
}

func gcAction(ctx context.Context, rr *types.ReconciliationRequest) error {
	// TODO: implement — use gc.NewAction to remove stale resources
	_ = gc.NewAction
	return nil
}
```

---

## Singleton Webhook (`internal/webhook/singleton.go`)

```go
package webhook

import (
	"context"

	"k8s.io/apimachinery/pkg/runtime/schema"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/webhook/admission"

	webhookutil "github.com/opendatahub-io/odh-platform-utilities/pkg/webhook"
)

var gvk = schema.GroupVersionKind{
	Group:   "<API_GROUP>",
	Version: "<API_VERSION>",
	Kind:    "<COMPONENT_PASCAL>",
}

type SingletonWebhook struct {
	Reader client.Reader
}

func (w *SingletonWebhook) Handle(ctx context.Context, req admission.Request) admission.Response {
	return webhookutil.ValidateSingletonCreation(ctx, w.Reader, &req, gvk)
}
```

---

## Main (`cmd/main.go`)

```go
package main

import (
	"flag"
	"os"

	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"

	<API_VERSION> "github.com/opendatahub-io/<MODULE_REPO>/api/<API_VERSION>"
	"github.com/opendatahub-io/<MODULE_REPO>/internal/controller"
)

var (
	scheme   = runtime.NewScheme()
	setupLog = ctrl.Log.WithName("setup")
)

func init() {
	utilruntime.Must(clientgoscheme.AddToScheme(scheme))
	utilruntime.Must(<API_VERSION>.AddToScheme(scheme))
}

func main() {
	var metricsAddr string
	var probeAddr string
	var enableLeaderElection bool

	flag.StringVar(&metricsAddr, "metrics-bind-address", ":8080", "The address the metric endpoint binds to.")
	flag.StringVar(&probeAddr, "health-probe-bind-address", ":8081", "The address the probe endpoint binds to.")
	flag.BoolVar(&enableLeaderElection, "leader-elect", false, "Enable leader election.")
	flag.Parse()

	ctrl.SetLogger(zap.New(zap.UseDevMode(true)))

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
		Metrics: metricsserver.Options{
			BindAddress: metricsAddr,
		},
		HealthProbeBindAddress: probeAddr,
		LeaderElection:         enableLeaderElection,
		LeaderElectionID:       "<COMPONENT>.platform.opendatahub.io",
	})
	if err != nil {
		setupLog.Error(err, "unable to start manager")
		os.Exit(1)
	}

	ctx := ctrl.SetupSignalHandler()

	if err := controller.SetupController(ctx, mgr); err != nil {
		setupLog.Error(err, "unable to create controller")
		os.Exit(1)
	}

	if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up health check")
		os.Exit(1)
	}
	if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up ready check")
		os.Exit(1)
	}

	setupLog.Info("starting manager")
	if err := mgr.Start(ctx); err != nil {
		setupLog.Error(err, "problem running manager")
		os.Exit(1)
	}
}
```

---

## Helm Chart Templates

### `charts/<MODULE_REPO>/templates/_helpers.tpl`

```text
{{- define "<MODULE_REPO>.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "<MODULE_REPO>.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "<MODULE_REPO>.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "<MODULE_REPO>.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "<MODULE_REPO>.selectorLabels" -}}
app.kubernetes.io/name: {{ include "<MODULE_REPO>.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

### `charts/<MODULE_REPO>/templates/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "<MODULE_REPO>.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "<MODULE_REPO>.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "<MODULE_REPO>.fullname" . }}
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: manager
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          args:
            - --leader-elect={{ .Values.leaderElect }}
            - --health-probe-bind-address=:8081
            - --metrics-bind-address=:8080
          ports:
            - containerPort: 8080
              name: metrics
              protocol: TCP
            - containerPort: 9443
              name: webhook
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8081
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8081
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          volumeMounts:
            - name: webhook-cert
              mountPath: /tmp/k8s-webhook-server/serving-certs
              readOnly: true
      volumes:
        - name: webhook-cert
          secret:
            secretName: {{ include "<MODULE_REPO>.fullname" . }}-webhook-cert
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### `charts/<MODULE_REPO>/templates/serviceaccount.yaml`

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
```

### `charts/<MODULE_REPO>/templates/clusterrole.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}-controller
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
rules:
  - apiGroups:
      - "<API_GROUP>"
    resources:
      - <COMPONENT_LOWER_PLURAL>
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete
  - apiGroups:
      - "<API_GROUP>"
    resources:
      - <COMPONENT_LOWER_PLURAL>/status
    verbs:
      - get
      - update
      - patch
  - apiGroups:
      - "<API_GROUP>"
    resources:
      - <COMPONENT_LOWER_PLURAL>/finalizers
    verbs:
      - update
  - apiGroups:
      - ""
    resources:
      - configmaps
    verbs:
      - get
      - list
      - watch
  - apiGroups:
      - coordination.k8s.io
    resources:
      - leases
    verbs:
      - get
      - list
      - watch
      - create
      - update
      - patch
      - delete
  - apiGroups:
      - ""
    resources:
      - events
    verbs:
      - create
      - patch
```

### `charts/<MODULE_REPO>/templates/clusterrolebinding.yaml`

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}-controller
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: {{ include "<MODULE_REPO>.fullname" . }}-controller
subjects:
  - kind: ServiceAccount
    name: {{ include "<MODULE_REPO>.fullname" . }}
    namespace: {{ .Release.Namespace }}
```

### `charts/<MODULE_REPO>/templates/webhook-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}-webhook
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
spec:
  ports:
    - port: 443
      targetPort: 9443
      protocol: TCP
      name: webhook
  selector:
    {{- include "<MODULE_REPO>.selectorLabels" . | nindent 4 }}
```

### `charts/<MODULE_REPO>/templates/webhook-certificate.yaml`

```yaml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}-selfsigned
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
spec:
  selfSigned: {}
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {{ include "<MODULE_REPO>.fullname" . }}-webhook-cert
  labels:
    {{- include "<MODULE_REPO>.labels" . | nindent 4 }}
spec:
  secretName: {{ include "<MODULE_REPO>.fullname" . }}-webhook-cert
  issuerRef:
    name: {{ include "<MODULE_REPO>.fullname" . }}-selfsigned
    kind: Issuer
  dnsNames:
    - {{ include "<MODULE_REPO>.fullname" . }}-webhook.{{ .Release.Namespace }}.svc
    - {{ include "<MODULE_REPO>.fullname" . }}-webhook.{{ .Release.Namespace }}.svc.cluster.local
```

### `charts/<MODULE_REPO>/values.yaml`

```yaml
replicaCount: 1

image:
  repository: quay.io/opendatahub/<MODULE_REPO>
  tag: latest
  pullPolicy: IfNotPresent

leaderElect: true

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

nodeSelector: {}
tolerations: []
```

---

## Sample CR (`config/samples/<COMPONENT_SNAKE>.yaml`)

```yaml
apiVersion: <API_GROUP>/<API_VERSION>
kind: <COMPONENT_PASCAL>
metadata:
  name: <SINGLETON_NAME>
spec:
  managementState: Managed
```

---

## AGENTS.md

Use the comprehensive template from
`module-compliance/references/agents-md-template.md`. Replace all
`<COMPONENT_PASCAL>` and `<component>` placeholders with the actual values.

The template covers: architecture context, shared library packages,
CRD rules, controller rules, Helm chart rules, security rules,
separation of concerns, testing patterns, and a code review checklist.

## .rules/ directory

Copy the following files from `module-compliance/references/rules/` into
the generated repo's `.rules/` directory:

- `api-types.md` -- triggers on `api/**/*.go`
- `controller.md` -- triggers on `internal/controller/**/*.go`
- `helm-chart.md` -- triggers on `charts/**`
- `security.md` -- triggers on `**/*.go` and `**/*.yaml`
- `testing.md` -- triggers on `**/*_test.go` and `tests/**/*.go`

These are path-scoped rules that fire automatically when AI agents edit
matching files, providing passive compliance enforcement without requiring
the developer to invoke anything.

---

## Containerfile

```dockerfile
FROM registry.access.redhat.com/ubi9/go-toolset:1.23 AS builder

WORKDIR /workspace
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -o manager cmd/main.go

FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=builder /workspace/manager .
USER 65532:65532
ENTRYPOINT ["/manager"]
```

---

## Makefile

```makefile
BINARY ?= manager
IMG ?= quay.io/opendatahub/<MODULE_REPO>:latest

.PHONY: build test lint manifests generate fmt vet docker-build docker-push helm-lint

build:
	go build -o bin/$(BINARY) cmd/main.go

test:
	go test -race -count=1 ./...

lint:
	golangci-lint run ./...

manifests:
	controller-gen rbac:roleName=manager-role crd webhook paths="./..." output:crd:artifacts:config=config/crd/bases

generate:
	controller-gen object paths="./..."

fmt:
	go fmt ./...

vet:
	go vet ./...

docker-build:
	podman build -t $(IMG) -f Containerfile .

docker-push:
	podman push $(IMG)

helm-lint:
	helm lint charts/<MODULE_REPO>
```

---

## .gitignore

```text
bin/
vendor/
*.exe
*.test
*.out
.idea/
.vscode/
```

---

## CI Workflow (`.github/workflows/ci.yaml`)

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions: read-all

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - uses: actions/setup-go@d35c59abb061a4a6fb18e82ac0862c26744d6ab5
        with:
          go-version-file: go.mod
      - uses: golangci/golangci-lint-action@4afd733a84b1f43292c63897423277bb7f4313a9
        with:
          version: v2.12.2

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - uses: actions/setup-go@d35c59abb061a4a6fb18e82ac0862c26744d6ab5
        with:
          go-version-file: go.mod
      - run: make test

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - uses: actions/setup-go@d35c59abb061a4a6fb18e82ac0862c26744d6ab5
        with:
          go-version-file: go.mod
      - run: make build
```
