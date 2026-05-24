# Conforma Policy Reference

Curated reference from [conforma.dev](https://conforma.dev) upstream documentation.

## What Is Conforma (Enterprise Contract)?

Conforma (formerly Enterprise Contract) is a policy verification tool for software supply chains. It evaluates container images and their build artifacts against a set of policies to ensure compliance with security, provenance, and quality standards.

## How Verification Works

1. A Konflux pipeline builds a container image
2. The `verify-enterprise-contract` Tekton task runs against the built image
3. Conforma evaluates the image against configured policies (Rego rules)
4. A verification report is produced listing pass/fail results per policy rule

## Common Policy Categories

- **Attestation tasks**: verify that required build tasks (SBOM generation, image signing) were present and succeeded
- **Signature checks**: verify that container images are properly signed
- **Provenance**: verify that build provenance metadata is present and valid
- **SLSA compliance**: verify that builds meet the specified SLSA level
- **Custom policies**: organization-specific rules

## Violation Severity Levels

- **failure**: the image cannot be released until this is resolved
- **warning**: advisory; does not block release but should be addressed

## Exceptions / Waivers

When a violation cannot or should not be fixed, an exception policy can be added to exempt a specific component from a specific rule. Exceptions are managed as policy configuration in a dedicated repository and go through a review process.

## Further Reading

- [Conforma User Guide](https://conforma.dev/docs/user-guide/)
- [Reproducing a Conforma Report](https://conforma.dev/docs/user-guide/reproducing-a-konflux-conforma-report.html)
- [Policy Rule Reference](https://conforma.dev/docs/ec-policies/release_policy.html)
