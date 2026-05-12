#!/usr/bin/env bash
set -euo pipefail

# Fetch JIRA data for all team members defined in a config file.
# Uses acli + jq. Outputs JSON to stdout.
#
# Prerequisites: acli (authenticated), jq, yq
#
# Usage:
#   fetch_team_jira.sh --config team-config.yaml
#   fetch_team_jira.sh --config team-config.yaml --days 14

usage() {
  >&2 echo "Usage: $(basename "$0") --config <path> [--days N]"
  exit 1
}

escape_jql() {
  printf '%s' "$1" | sed 's/[\\\"]/\\&/g'
}

run_search() {
  local jql="$1"
  local raw
  raw=$(acli jira workitem search --jql "$jql" --json --paginate 2>/dev/null) || raw="[]"
  echo "$raw" | jq '[.[] | {
    key: .key,
    summary: .fields.summary,
    status: (.fields.status.name // ""),
    assignee: (.fields.assignee.displayName // ""),
    priority: (.fields.priority.name // "")
  }]' 2>/dev/null || echo "[]"
}

date_days_ago() {
  local days="$1"
  date -u -v-"${days}"d +%Y-%m-%d 2>/dev/null \
    || date -u -d "$days days ago" +%Y-%m-%d
}

# --- Parse arguments ---
CONFIG=""
DAYS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="${2:-}"; shift 2 ;;
    --days)   DAYS="${2:-}"; shift 2 ;;
    *)        usage ;;
  esac
done

[[ -z "$CONFIG" ]] && usage
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

TEAM_NAME=$(echo "$CONFIG_JSON" | jq -r '.team.name // ""')
JIRA_URL=$(echo "$CONFIG_JSON" | jq -r '(.team.jira.url // .jira.url) // ""')
PROJECT=$(echo "$CONFIG_JSON" | jq -r '(.team.jira.project // .jira.project_key // .jira.project) // ""')
COMPONENT=$(echo "$CONFIG_JSON" | jq -r '(.team.jira.component // .jira.component) // ""')

[[ -z "$JIRA_URL" || -z "$PROJECT" ]] \
  && { >&2 echo "ERROR: Config missing jira url or project. Set team.jira.url/project or jira.url/project_key."; exit 1; }

# --- Compute lookback/stale days ---
DEFAULT_LOOKBACK=$(echo "$CONFIG_JSON" | jq -r '(.defaults.jira_lookback_days // .report.lookback_days) // 7')
DEFAULT_STALE=$(echo "$CONFIG_JSON" | jq -r '.defaults.stale_threshold_days // empty')

LOOKBACK_DAYS="${DAYS:-$DEFAULT_LOOKBACK}"
if ! [[ "$LOOKBACK_DAYS" =~ ^[0-9]+$ ]]; then LOOKBACK_DAYS=7; fi
LOOKBACK_DAYS=$(( LOOKBACK_DAYS < 1 ? 1 : (LOOKBACK_DAYS > 365 ? 365 : LOOKBACK_DAYS) ))

STALE_DAYS="${DEFAULT_STALE:-$LOOKBACK_DAYS}"
if ! [[ "$STALE_DAYS" =~ ^[0-9]+$ ]]; then STALE_DAYS="$LOOKBACK_DAYS"; fi
STALE_DAYS=$(( STALE_DAYS < 1 ? 1 : (STALE_DAYS > 365 ? 365 : STALE_DAYS) ))

NOW=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
CUTOFF_DATE=$(date_days_ago "$LOOKBACK_DAYS")
STALE_DATE=$(date_days_ago "$STALE_DAYS")

# --- Build JQL fragments ---
SAFE_PROJECT=$(escape_jql "$PROJECT")
COMPONENT_CLAUSE=""
if [[ -n "$COMPONENT" ]]; then
  COMPONENT_CLAUSE=" AND component = \"$(escape_jql "$COMPONENT")\""
fi

# --- Fetch per-member data ---
MEMBER_COUNT=$(echo "$CONFIG_JSON" | jq '.team.members | length')
>&2 echo "Fetching JIRA data for $MEMBER_COUNT team members..."

WORK=$(mktemp -d)
trap 'rm -rf -- "$WORK"' EXIT

for i in $(seq 0 $((MEMBER_COUNT - 1))); do
  NAME=$(echo "$CONFIG_JSON" | jq -r ".team.members[$i].name // \"unknown\"")
  USERNAME=$(echo "$CONFIG_JSON" | jq -r ".team.members[$i].jira_username // \"\"")

  >&2 echo "  Fetching data for $NAME..."

  if [[ -z "$USERNAME" ]]; then
    jq -n --arg name "$NAME" \
      '{"name": $name, "error": "No jira_username configured"}' \
      > "$WORK/member_$i.json"
    continue
  fi

  SAFE_USERNAME=$(escape_jql "$USERNAME")
  BASE="project = \"$SAFE_PROJECT\"$COMPONENT_CLAUSE AND assignee = \"$SAFE_USERNAME\""
  SAFE_CUTOFF=$(escape_jql "$CUTOFF_DATE")
  SAFE_STALE=$(escape_jql "$STALE_DATE")

  CLOSED=$(run_search "$BASE AND status changed to (Done, Closed) AFTER \"$SAFE_CUTOFF\"")
  OPEN=$(run_search "$BASE AND status NOT IN (Done, Closed)")
  STALE=$(run_search "$BASE AND status NOT IN (Done, Closed) AND updated < \"$SAFE_STALE\"")
  BLOCKED=$(run_search "$BASE AND status = \"Blocked\"")

  jq -n \
    --arg name "$NAME" \
    --arg username "$USERNAME" \
    --argjson closed "$CLOSED" \
    --argjson open_issues "$OPEN" \
    --argjson stale "$STALE" \
    --argjson blocked "$BLOCKED" \
    '{
      name: $name,
      jira_username: $username,
      closed_issues: $closed,
      open_issues: $open_issues,
      stale_issues: $stale,
      blocked_issues: $blocked
    }' > "$WORK/member_$i.json"
done

# --- Combine results ---
MEMBERS=$(jq -s '.' "$WORK"/member_*.json 2>/dev/null || echo "[]")

jq -n \
  --arg team_name "$TEAM_NAME" \
  --arg fetched_at "$NOW" \
  --argjson lookback_days "$LOOKBACK_DAYS" \
  --argjson stale_days "$STALE_DAYS" \
  --arg jira_url "$JIRA_URL" \
  --arg project "$PROJECT" \
  --arg component "$COMPONENT" \
  --argjson members "$MEMBERS" \
  '{
    team_name: $team_name,
    metadata: {
      fetched_at: $fetched_at,
      lookback_days: $lookback_days,
      stale_threshold_days: $stale_days,
      jira_url: $jira_url,
      project: $project,
      component: $component
    },
    members: $members
  }'
