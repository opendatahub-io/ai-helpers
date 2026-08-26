#!/usr/bin/env bash
set -euo pipefail

# Fetch JIRA data for a single engineer from the team config.
# Uses acli + jq. Outputs JSON to stdout.
# Uses two-pass (search + view) to get created/updated dates for days_open.
#
# Prerequisites: acli (authenticated), jq, yq
#
# Usage:
#   fetch_engineer_jira.sh --config team-config.yaml --engineer "Engineer One"

usage() {
  >&2 echo "Usage: $(basename "$0") --config <path> --engineer <name>"
  exit 1
}

escape_jql() {
  printf '%s' "$1" | sed 's/[\\\"]/\\&/g'
}

search_and_view() {
  local jql="$1"
  local now_epoch="$2"
  local keys

  keys=$(acli jira workitem search --jql "$jql" --json --paginate 2>/dev/null \
    | jq -r '.[].key' 2>/dev/null) || keys=""

  if [[ -z "$keys" ]]; then
    echo "[]"
    return
  fi

  local results="[]"
  local key
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    local issue
    issue=$(acli jira workitem view "$key" \
      --fields key,summary,status,assignee,priority,created,updated \
      --json 2>/dev/null) || continue

    local formatted
    formatted=$(echo "$issue" | jq --argjson now_epoch "$now_epoch" '{
      key: .key,
      summary: .fields.summary,
      status: (.fields.status.name // ""),
      assignee: (.fields.assignee.displayName // ""),
      priority: (.fields.priority.name // ""),
      created: (.fields.created // ""),
      updated: (.fields.updated // ""),
      days_open: (
        if .fields.created then
          (($now_epoch - (.fields.created | split(".")[0] | split("+")[0] | . + "Z" | fromdate)) / 86400 | floor)
        else null end
      )
    }' 2>/dev/null) || continue

    results=$(echo "$results" | jq --argjson item "$formatted" '. + [$item]')
  done <<< "$keys"

  echo "$results"
}

# --- Parse arguments ---
CONFIG=""
ENGINEER=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)   CONFIG="${2:-}"; shift 2 ;;
    --engineer) ENGINEER="${2:-}"; shift 2 ;;
    *)          usage ;;
  esac
done

[[ -z "$CONFIG" ]] && usage
[[ -z "$ENGINEER" ]] && usage
[[ ! -f "$CONFIG" ]] && { >&2 echo "ERROR: Config file not found: $CONFIG"; exit 1; }

# --- Check dependencies ---
for cmd in acli jq yq; do
  command -v "$cmd" >/dev/null 2>&1 \
    || { >&2 echo "ERROR: $cmd is required but not found."; exit 1; }
done

# --- Parse config ---
CONFIG_JSON=$(yq -o=json '.' "$CONFIG")

if ! echo "$CONFIG_JSON" | jq -e '.team' >/dev/null 2>&1; then
  >&2 echo "ERROR: Config missing 'team' key."
  exit 1
fi

JIRA_URL=$(echo "$CONFIG_JSON" | jq -r '(.team.jira.url // .jira.url) // ""')
PROJECT=$(echo "$CONFIG_JSON" | jq -r '(.team.jira.project // .jira.project_key // .jira.project) // ""')
COMPONENT=$(echo "$CONFIG_JSON" | jq -r '(.team.jira.component // .jira.component) // ""')

[[ -z "$JIRA_URL" || -z "$PROJECT" ]] \
  && { >&2 echo "ERROR: Config missing jira url or project. Set team.jira.url/project or jira.url/project_key."; exit 1; }

# --- Find member by name (case-insensitive) ---
ENGINEER_LOWER=$(echo "$ENGINEER" | tr '[:upper:]' '[:lower:]')

MEMBER_JSON=$(echo "$CONFIG_JSON" | jq --arg name "$ENGINEER_LOWER" '
  .team.members
  | (map(select((.name // "") | ascii_downcase == $name)) | first) //
    (
      [.[] | select((.name // "") | ascii_downcase | contains($name))]
      | if length == 1 then .[0] else null end
    )
')

if [[ "$MEMBER_JSON" == "null" || -z "$MEMBER_JSON" ]]; then
  AVAILABLE=$(echo "$CONFIG_JSON" | jq -r '[.team.members[].name] | join(", ")')
  >&2 echo "ERROR: Engineer '$ENGINEER' not found. Available: $AVAILABLE"
  exit 1
fi

NAME=$(echo "$MEMBER_JSON" | jq -r '.name // ""')
USERNAME=$(echo "$MEMBER_JSON" | jq -r '.jira_username // ""')
GH_USER=$(echo "$MEMBER_JSON" | jq -r '.github_username // ""')
NOTES_FILE=$(echo "$MEMBER_JSON" | jq -r '.notes_file // ""')

if [[ -z "$USERNAME" ]]; then
  >&2 echo "ERROR: No jira_username configured for '$NAME'."
  exit 1
fi

# --- Build JQL ---
SAFE_PROJECT=$(escape_jql "$PROJECT")
SAFE_USERNAME=$(escape_jql "$USERNAME")
COMPONENT_CLAUSE=""
if [[ -n "$COMPONENT" ]]; then
  COMPONENT_CLAUSE=" AND component = \"$(escape_jql "$COMPONENT")\""
fi
BASE="project = \"$SAFE_PROJECT\"$COMPONENT_CLAUSE AND assignee = \"$SAFE_USERNAME\""

NOW=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
NOW_EPOCH=$(date -u +%s)

>&2 echo "Fetching JIRA data for $NAME..."

ACTIVE_ISSUES=$(search_and_view "$BASE AND status NOT IN (Done, Closed)" "$NOW_EPOCH")
BLOCKED_ISSUES=$(search_and_view "$BASE AND status = \"Blocked\"" "$NOW_EPOCH")

ACTIVE_COUNT=$(echo "$ACTIVE_ISSUES" | jq 'length')
BLOCKED_COUNT=$(echo "$BLOCKED_ISSUES" | jq 'length')

# --- Output ---
jq -n \
  --arg name "$NAME" \
  --arg username "$USERNAME" \
  --arg gh_user "$GH_USER" \
  --arg notes_file "$NOTES_FILE" \
  --arg fetched_at "$NOW" \
  --arg jira_url "$JIRA_URL" \
  --arg project "$PROJECT" \
  --arg component "$COMPONENT" \
  --argjson active "$ACTIVE_ISSUES" \
  --argjson blocked "$BLOCKED_ISSUES" \
  --argjson active_count "$ACTIVE_COUNT" \
  --argjson blocked_count "$BLOCKED_COUNT" \
  '{
    engineer: {
      name: $name,
      jira_username: $username,
      github_username: $gh_user,
      notes_file: $notes_file
    },
    metadata: {
      fetched_at: $fetched_at,
      jira_url: $jira_url,
      project: $project,
      component: $component
    },
    active_issues: $active,
    blocked_issues: $blocked,
    summary: {
      active_count: $active_count,
      blocked_count: $blocked_count
    }
  }'
