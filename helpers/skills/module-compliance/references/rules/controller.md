---
paths: ["internal/controller/**/*.go"]
---

# Module Controller Patterns

Use `reconciler.NewReconciler` from `framework/controller/reconciler` with
functional options. Actions execute sequentially and stop on first error.

Three standard actions: render, deploy, gc. **GC action MUST be last.** Deploy
stamps lifecycle annotations that GC reads to detect stale resources. Running
GC before deploy deletes resources that are about to be re-created.

Configure conditions via `WithConditionsManagerFactory`:

```go
r, err := reconciler.NewReconciler(mgr, "component", &v1alpha1.Component{},
    reconciler.WithConditionsManagerFactory(
        string(common.ConditionTypeReady),              // happy condition
        string(common.ConditionTypeProvisioningSucceeded), // dependent
        string(common.ConditionTypeDegraded),           // dependent
    ),
    reconciler.WithRelease(release),
    reconciler.WithDynamicOwnership(),
)
r.AddAction(renderAction)
r.AddAction(deployAction)
r.AddAction(gcAction) // must be last
```

`ProvisioningSucceeded` MUST aggregate into `Ready`. `Degraded` COULD
aggregate depending on severity.

Every condition update must include `ObservedGeneration` from the CR's
`.metadata.generation`.

Update `status.observedGeneration = cr.Generation` on every successful
reconcile.

Use `framework/controller/actions/deploy` for resource deployment via SSA.
Use `framework/controller/actions/render` for Helm/Kustomize rendering.
Use `framework/controller/actions/gc` for garbage collection.

Use `pkg/cluster` for environment detection (OpenShift, FIPS, etc.). The
module performs its own detection -- do not rely on the orchestrator to pass
this information.

Handle missing dependencies gracefully: set `Degraded=True` or `Ready=False`
with a clear Reason. Never `panic`, `os.Exit`, or `log.Fatal` on a missing
dependency.

Import types from `odh-platform-utilities`, not from the operator's internal
packages. No imports from `opendatahub-operator/internal/`.
