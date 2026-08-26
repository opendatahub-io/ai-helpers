#!/usr/bin/env bash
set -euo pipefail

# Fetch GitHub PR data for all team members using the gh CLI.
# Outputs JSON to stdout for the team-weekly-report skill.
#
# Prerequisites: gh (authenticated), jq, yq
#
# Usage:
#   fetch_team_github.sh --config team-config.yaml
#   fetch_team_github.sh --config team-config.yaml --days 14

GH_DELAY=0.5

usage() {
  >&2 echo "Usage: $(basename "$0") --config <path> [--days N]"
  exit 1
}

date_days_ago() {
  local days="$1"
  date -u -v-"${days}"d +%Y-%m-%d 2>/dev/null \
    || date -u -d "$days days ago" +%Y-%m-%d
}

run_gh() {
  local output
  output=$(gh "$@" 2>/dev/null) || output="[]"
  if [[ -z "$output" ]]; then
    echo "[]"
  else
    echo "$output"
  fi
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
for cmd in gh jq yq; do
  command -v "$cmd" >/dev/null 2>&1 \
    || { >&2 echo "ERROR: $cmd is required but not found."; exit 1; }
done

# --- Verify gh auth ---
if ! gh auth status >/dev/null 2>&1; then
  >&2 echo "ERROR: gh CLI is not authenticated. Run: gh auth login"
  exit 1
fi

# --- Parse config ---
CONFIG_JSON=$(yq -o=json '.' "$CONFIG")

if ! echo "$CONFIG_JSON" | jq -e '.team' >/dev/null 2>&1; then
  >&2 echo "ERROR: Config missing 'team' key."
  exit 1
fi

# --- Compute lookback ---
DEFAULT_LOOKBACK=$(echo "$CONFIG_JSON" | jq -r '(.defaults.github_lookback_days // .report.lookback_days) // 7')
LOOKBACK_DAYS="${DAYS:-$DEFAULT_LOOKBACK}"
if ! [[ "$LOOKBACK_DAYS" =~ ^[0-9]+$ ]]; then LOOKBACK_DAYS=7; fi
LOOKBACK_DAYS=$(( LOOKBACK_DAYS < 1 ? 1 : (LOOKBACK_DAYS > 365 ? 365 : LOOKBACK_DAYS) ))

NOW=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)
CUTOFF_DATE=$(date_days_ago "$LOOKBACK_DAYS")

REPOS_JSON=$(echo "$CONFIG_JSON" | jq '(.team.github.repositories // .github.repositories) // []')
REPO_COUNT=$(echo "$REPOS_JSON" | jq 'length')
MEMBER_COUNT=$(echo "$CONFIG_JSON" | jq '.team.members | length')

>&2 echo "Fetching GitHub PRs for $MEMBER_COUNT members across $REPO_COUNT repos..."

WORK=$(mktemp -d)
trap 'rm -rf -- "$WORK"' EXIT

for i in $(seq 0 $((MEMBER_COUNT - 1))); do
  NAME=$(echo "$CONFIG_JSON" | jq -r ".team.members[$i].name // \"unknown\"")
  GH_USER=$(echo "$CONFIG_JSON" | jq -r ".team.members[$i].github_username // \"\"")

  if [[ -z "$GH_USER" ]]; then
    jq -n --arg name "$NAME" \
      '{"name": $name, "error": "No github_username configured"}' \
      > "$WORK/member_$i.json"
    continue
  fi

  >&2 echo "  Fetching PRs for $NAME ($GH_USER)..."

  OPEN_PRS="[]"
  MERGED_PRS="[]"

  for j in $(seq 0 $((REPO_COUNT - 1))); do
    REPO=$(echo "$CONFIG_JSON" | jq -r ".team.github.repositories[$j]")

    # Open PRs
    BATCH=$(run_gh search prs \
      "--author=$GH_USER" \
      "--repo=$REPO" \
      --state=open \
      "--json=number,title,url,createdAt,updatedAt,labels" \
      --limit 100)
    BATCH=$(echo "$BATCH" | jq --arg repo "$REPO" --arg author "$GH_USER" \
      '[.[] | . + {repo: $repo, author: $author}]')
    OPEN_PRS=$(echo "$OPEN_PRS" "$BATCH" | jq -s 'add')
    sleep "$GH_DELAY"

    # Merged PRs within lookback window
    BATCH=$(run_gh pr list \
      "-R=$REPO" \
      "-A=$GH_USER" \
      --state=merged \
      "--json=number,title,url,createdAt,mergedAt,labels" \
      --limit 100 \
      "-S=merged:>=$CUTOFF_DATE")
    BATCH=$(echo "$BATCH" | jq --arg repo "$REPO" --arg author "$GH_USER" \
      '[.[] | . + {repo: $repo, author: $author}]')
    MERGED_PRS=$(echo "$MERGED_PRS" "$BATCH" | jq -s 'add')
    sleep "$GH_DELAY"
  done

  jq -n \
    --arg name "$NAME" \
    --arg gh_user "$GH_USER" \
    --argjson open_prs "$OPEN_PRS" \
    --argjson merged_prs "$MERGED_PRS" \
    '{
      name: $name,
      github_username: $gh_user,
      open_prs: $open_prs,
      merged_prs: $merged_prs
    }' > "$WORK/member_$i.json"
done

# --- Combine results ---
MEMBERS=$(jq -s '.' "$WORK"/member_*.json 2>/dev/null || echo "[]")

jq -n \
  --arg fetched_at "$NOW" \
  --argjson lookback_days "$LOOKBACK_DAYS" \
  --arg cutoff_date "$CUTOFF_DATE" \
  --argjson repos "$REPOS_JSON" \
  --argjson members "$MEMBERS" \
  '{
    metadata: {
      fetched_at: $fetched_at,
      lookback_days: $lookback_days,
      cutoff_date: $cutoff_date,
      repositories: $repos
    },
    members: $members
  }'
