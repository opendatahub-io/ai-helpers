# Downstream repo locations for MaaS nightly QE

Static map of where MaaS-related nightly infrastructure lives. Use during hybrid
search to link concrete file paths in PR descriptions.

## opendatahub-tests

Repository: https://github.com/opendatahub-io/opendatahub-tests

| Area | Path | Notes |
|------|------|-------|
| MaaS billing tests (all) | `tests/model_serving/maas_billing/` | Primary nightly test tree |
| Component health | `tests/model_serving/maas_billing/component_health/` | maas-api/controller deployment checks |
| Multitenancy | `tests/model_serving/maas_billing/multitenancy/` | Per-tenant maas-api, AITenant, isolation |
| Upgrade tests | `tests/model_serving/maas_billing/upgrade/` | Post-upgrade deployment availability |
| API keys / auth | `tests/model_serving/maas_billing/maas_api_key/` | AuthPolicy callback URLs |
| Subscriptions | `tests/model_serving/maas_billing/maas_subscription/` | Model access enforcement |
| Shared utilities | `tests/model_serving/maas_billing/utils.py` | Common helpers, gateway URLs |
| Multitenancy utils | `tests/model_serving/maas_billing/multitenancy/utils.py` | Deployment names, namespace helpers |
| Gateway constants | `utilities/constants.py` (search `MAAS_GATEWAY`) | Shared MAAS_GATEWAY_NAME/NAMESPACE |

**Search focus terms:** `maas-api`, `maas-controller`, `maas-db-config`,
`INFRA_NAMESPACE`, `MAAS_NAMESPACE`, `MaaSAuthPolicy`, `Tenant`, gateway hostname.

## ods-ci

Repository: https://github.com/red-hat-data-services/ods-ci

| Area | Path | Notes |
|------|------|-------|
| MaaS postgres provisioning | `ods_ci/tasks/Resources/Database/configure_maas_postgres.sh` | Creates `maas-db-config` in infra NS |
| MaaS gateway setup | `ods_ci/tasks/Resources/Gateway/configure_maas_gateway.sh` | Gateway, Route, Authorino TLS |
| OLM install hooks | `ods_ci/tasks/Resources/RHODS_OLM/install/oc_install.robot` | Calls MaaS setup scripts |
| DSC component checks | `ods_ci/tests/Tests/0100__platform/0101__deploy/0104__operators/0104__rhods_operator/0113__dsc_components.robot` | MaaS deployment health |

**Search focus terms:** `maas-db-config`, `derive_infra_namespace`,
`INFRA_NAMESPACE`, `configure_maas`, `maas-api`, `APPLICATIONS_NAMESPACE`.

## Known cross-repo coupling examples

| Product change | Required downstream update |
|----------------|---------------------------|
| Infra namespace separation (#1051) | ods-ci: `configure_maas_postgres.sh` puts secret in infra NS; tests: use `INFRA_NAMESPACE` not `MAAS_NAMESPACE` for maas-api lookups |
| NetworkPolicy label fix | opendatahub-tests: run curl from allowed namespace (e.g. `openshift-ingress`) |
| CRD field rename | opendatahub-tests: update struct literals and test fixtures |
| New MaaS API endpoint | opendatahub-tests: add or update tests under relevant `maas_billing/` subdir |

## Link format for PR descriptions

Use GitHub blob links with `main` branch (merge team can adjust branch):

```
https://github.com/opendatahub-io/opendatahub-tests/blob/main/tests/model_serving/maas_billing/component_health/test_maas_api_health_check.py
https://github.com/red-hat-data-services/ods-ci/blob/master/ods_ci/tasks/Resources/Database/configure_maas_postgres.sh
```

Note: ods-ci default branch is `master`; opendatahub-tests uses `main`.
