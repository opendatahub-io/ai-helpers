# MaaS change triggers for nightly QE impact

Use this catalog during diff analysis. A match in **any** row warrants flagging
for human follow-up in the listed downstream repo(s).

## Namespace and deployment topology

| Trigger | Why nightlies break | Downstream repo |
|---------|---------------------|-----------------|
| `INFRA_NAMESPACE`, `MAAS_NAMESPACE`, `--infra-namespace` | Tests/CI scripts assume maas-api and secrets live in controller namespace | Both |
| `odh-ai-gateway-infra`, `redhat-ai-gateway-infra` | Hardcoded namespace constants in tests and install scripts | Both |
| Moves of `maas-api`, `maas-controller`, `maas-db-config` between namespaces | Health checks and kubectl probes target wrong namespace | Both |
| Kustomize component `infra-namespace-separation` | Nightly install path must enable matching separation | ods-ci |
| Changes to `derive_infra_namespace` / `deriveInfraNamespace` | AUTO mapping must stay in sync across Go, shell, and CI | Both |

**Incident:** [models-as-a-service#1051](https://github.com/opendatahub-io/models-as-a-service/pull/1051) moved
`maas-db-config` to the infra namespace; nightlies failed until
[ods-ci#2987](https://github.com/red-hat-data-services/ods-ci/pull/2987) updated
`configure_maas_postgres.sh` and test namespace constants were fixed.

## Secrets and database

| Trigger | Why nightlies break | Downstream repo |
|---------|---------------------|-----------------|
| `maas-db-config` secret name, keys, or namespace | ods-ci provisioning creates secret in expected namespace | ods-ci |
| `DB_CONNECTION_URL` format (FQDN vs short service name) | Cross-namespace postgres requires FQDN in connection string | ods-ci |
| `setup-database.sh`, `configure_maas_postgres.sh` parity | Manual deploy scripts and CI provisioning must agree | ods-ci |
| PostgreSQL prerequisite changes | Nightly cluster bootstrap may miss new requirements | ods-ci |

## Networking

| Trigger | Why nightlies break | Downstream repo |
|---------|---------------------|-----------------|
| `NetworkPolicy` for maas-api or Gateway | Curl/test pods from wrong namespace get blocked (HTTP 0) | opendatahub-tests |
| Gateway pod label selectors (`gateway.istio.io/managed`, etc.) | Policy must match actual Gateway pod labels | Both |
| `configure_maas_gateway.sh` changes | Nightly gateway bootstrap may not match product | ods-ci |
| Route/hostname changes for `maas.<domain>` | External URL fixtures break | Both |

## API and CRD changes

| Trigger | Why nightlies break | Downstream repo |
|---------|---------------------|-----------------|
| New/changed REST paths under `/v1/` or `/internal/v1/` | Test clients call old endpoints | opendatahub-tests |
| CRD field renames (e.g. `MaaSAPINamespace` → `InfraNamespace`) | Test helpers reference old field names | opendatahub-tests |
| MaaSAuthPolicy, Tenant, MaaSSubscription schema changes | Subscription/auth enforcement tests assert old shape | opendatahub-tests |
| Rate limit or auth middleware changes | Token/API key tests may need new expectations | opendatahub-tests |

## Install and operator integration

| Trigger | Why nightlies break | Downstream repo |
|---------|---------------------|-----------------|
| DSC/DataScienceCluster component config for MaaS | ods-ci operator install checks component health | ods-ci |
| Metrics/monitoring prerequisites | Component health tests fail on missing DSCI config | ods-ci |
| `deploy.sh` env vars or default flags | Nightly deploy uses these scripts | ods-ci |
| Image tag or bundle reference changes | CI may pin old images | ods-ci |

## When impact is unlikely

Skip downstream flagging when the diff is limited to:

- Unit tests only under `maas-controller/` with no manifest/script changes
- Documentation-only changes under `docs/`
- Comment or logging changes with no behavioral effect
- Internal refactor with no namespace, API, CRD, or deploy surface change

When uncertain, classify as **Investigate** rather than **No impact**.
