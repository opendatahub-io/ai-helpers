---
paths: ["**/*_test.go", "tests/**/*.go"]
---

# Module Testing Patterns

Unit tests: use `fake.NewClientBuilder()` with explicit scheme registration.
Register schemes via a shared test helper to avoid duplication.

E2E test oracles MUST be structurally independent from production code. Never
call the same production function or read the same API resource as the code
under test -- derive expectations from independent signals.

Use `t.Parallel()` in all test functions and subtests.

Prefer table-driven tests for variations of the same assertion.

Place tests in the `_test` package suffix to exercise the public API.

Use `github.com/stretchr/testify/assert` and `require` for assertions.

Verify that status conditions are updated correctly during:
- Successful reconciliation (Ready=True, ProvisioningSucceeded=True)
- Failed provisioning (Ready=False, ProvisioningSucceeded=False)
- Degraded state (Ready=True, Degraded=True)
- Deletion (conditions cleaned up or set appropriately)
- Missing dependencies (Degraded=True or Ready=False with clear Reason)
