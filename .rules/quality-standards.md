# Quality Standards

These guidelines help reviewers focus on issues that automated linting
(claudelint, shellcheck, ruff, `make update`) cannot catch.

## Review Focus

**Shell Scripts:**
- Use `mktemp -d`, never hardcoded `/tmp/` paths
- Use `grep -E` instead of `grep -P` (macOS compatibility)
- Never `git add -A` in scripts — stage specific files only
- Do not suppress errors from `gh`, `curl`, or `git` — propagate failures

**Python Scripts:**
- Add timeouts to HTTP requests (`timeout=30`)
- Specify `encoding="utf-8"` when opening files
- Validate inputs before use in shell commands or API calls

**Skills and Commands:**
- `allowed_tools` must follow least-privilege principle
- Use team/org identifiers in `metadata.author`, not personal names

**Containerfiles / CI Workflows:**
- Pin base images by digest, not mutable tags
- Verify integrity of downloaded binaries (checksum or GPG signature)
- Pin GitHub Actions to full 40-character commit SHAs, not version tags
- Pin inline script dependencies to specific versions

## Common Issues to Flag

- Orphaned test files that will never be executed
- Unnecessary external dependencies in simple scripts
- References to real people by name (see ETHICS.md)
