#!/usr/bin/env bash
set -euo pipefail
# Emitted at SessionStart while the deprecated odh-ai-helpers umbrella is enabled.
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"NOTICE: the 'odh-ai-helpers' umbrella plugin is DEPRECATED and will be removed after the migration window. It re-exports the individual ODH AI Helpers plugins under the legacy odh-ai-helpers:* names. Install just the plugins you need (e.g. odh-jira, odh-python-packaging, odh-vllm, odh-git), then disable/uninstall odh-ai-helpers. Please inform the user of this deprecation notice once per session."}}
JSON
