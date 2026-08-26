#!/usr/bin/env bash
# Resolve a Jira ticket via REST API and emit structured JSON.
#
# Usage:
#   bash resolve-jira.sh RHOAIENG-55490
#
# Requires JIRA_EMAIL and JIRA_TOKEN environment variables (loaded from .env).
#
# Output (JSON to stdout):
# {
#   "key": "RHOAIENG-55490",
#   "summary": "...",
#   "description": "...",
#   "acceptance_criteria": "...",
#   "fix_versions": ["rhoai-2.18"],
#   "components": ["Dashboard", "Model Serving"],
#   "linked_tickets": ["RHOAIENG-12345"],
#   "epic_key": "RHOAIENG-55000",
#   "status": "In Progress",
#   "issue_type": "Story"
# }

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load .env if available (credentials, JIRA_URL, etc.)
# shellcheck disable=SC1091
source "${SCRIPTS_DIR}/load-env.sh"

TICKET_KEY="${1:?Usage: resolve-jira.sh <JIRA-KEY>}"

# Validate Jira ticket key format (e.g., PROJECT-123)
if ! [[ "${TICKET_KEY}" =~ ^[A-Z][A-Z0-9]+-[0-9]+$ ]]; then
    echo "Error: Invalid JIRA key format: ${TICKET_KEY}" >&2
    exit 1
fi

# When MCP is not available, attempt to use the Jira REST API directly.
# Requires JIRA_URL, JIRA_EMAIL, JIRA_TOKEN environment variables.
JIRA_URL="${JIRA_URL:-https://issues.redhat.com}"

if ! [[ "${JIRA_URL}" =~ ^https?:// ]]; then
    echo "Error: JIRA_URL must use http or https." >&2
    exit 1
fi

if [[ -z "${JIRA_EMAIL:-}" ]] || [[ -z "${JIRA_TOKEN:-}" ]]; then
    echo "Error: JIRA_EMAIL and JIRA_TOKEN must be set (add them to .env)." >&2
    exit 1
fi

# Fetch the issue
RESPONSE=$(curl --silent --show-error --fail \
    --connect-timeout 10 --max-time 30 \
    -u "${JIRA_EMAIL}:${JIRA_TOKEN}" \
    -H "Content-Type: application/json" \
    "${JIRA_URL}/rest/api/2/issue/${TICKET_KEY}?fields=summary,description,fixVersions,components,issuelinks,status,issuetype,parent") || {
    echo "Error: curl request failed for ticket ${TICKET_KEY}" >&2
    exit 1
}

if echo "$RESPONSE" | jq -e '.errorMessages' >/dev/null 2>&1; then
    echo "Error fetching ticket ${TICKET_KEY}:" >&2
    echo "$RESPONSE" | jq -r '.errorMessages[]' >&2
    exit 1
fi

# Extract fields into structured JSON
echo "$RESPONSE" | jq '{
    key: .key,
    summary: .fields.summary,
    description: (.fields.description // ""),
    acceptance_criteria: "",
    fix_versions: [.fields.fixVersions[]?.name],
    components: [.fields.components[]?.name],
    linked_tickets: [.fields.issuelinks[]? | (.outwardIssue.key // .inwardIssue.key) | select(. != null)],
    epic_key: (.fields.parent.key // ""),
    status: .fields.status.name,
    issue_type: .fields.issuetype.name
}'
