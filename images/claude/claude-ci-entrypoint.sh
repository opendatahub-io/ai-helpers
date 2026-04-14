#!/bin/bash
# Entrypoint wrapper for the Claude Code container image.
#
# By default, passes through to `claude` directly (identical to the
# previous ENTRYPOINT ["claude"]).
#
# When CLAUDE_CI_STREAM=1 is set, enables human-readable streaming
# output suitable for CI pipelines.  The wrapper automatically adds
# the required stream-json flags and pipes Claude's output through
# a parser that renders thinking, tool use, token stats, and errors
# as readable CI log lines.
#
# Environment variables (CI streaming mode only):
#   CLAUDE_CI_STREAM=1       Enable streaming mode
#   CLAUDE_CI_LOG_FILE       Write plain-text log (no ANSI) to this path
#   CLAUDE_CI_WRAP           Word-wrap output at N columns (0 = off)
#   NO_COLOR=1               Disable ANSI color codes

set -euo pipefail

# --- Non-streaming mode: transparent passthrough ---
if [[ "${CLAUDE_CI_STREAM:-}" != "1" ]]; then
    exec claude "$@"
fi

# --- CI streaming mode ---

# Build stream-claude.py arguments from environment.
stream_args=()
[[ -n "${CLAUDE_CI_LOG_FILE:-}" ]] && stream_args+=(--log-file "$CLAUDE_CI_LOG_FILE")
[[ -n "${CLAUDE_CI_WRAP:-}" ]]     && stream_args+=(--wrap "$CLAUDE_CI_WRAP")
[[ "${NO_COLOR:-}" == "1" ]]       && stream_args+=(--no-color)

# Create a FIFO so we can run claude and the stream parser as
# independent processes — this lets us track exit codes separately.
fifo=$(mktemp -u).fifo
mkfifo "$fifo"
trap 'rm -f "$fifo"' EXIT

# Run claude with stream-json output directed to the FIFO.
claude \
    --output-format stream-json \
    --include-partial-messages \
    --include-hook-events \
    --verbose \
    "$@" > "$fifo" &
claude_pid=$!

# Run the stream parser in the background.  Both children must be
# backgrounded so that bash can respond to signals — bash defers
# trap handlers while a foreground command is running, but processes
# them immediately when blocked on `wait`.
python3 -u /opt/ai-helpers/images/claude/stream-claude.py "${stream_args[@]}" < "$fifo" &
stream_pid=$!

# Forward signals to children.  As PID 1 in a container, this
# process does not get default signal handlers — SIGTERM must be
# explicitly caught and forwarded.
# shellcheck disable=SC2317  # invoked indirectly via trap
_on_signal() {
    kill "$claude_pid" "$stream_pid" 2>/dev/null || true
}
trap '_on_signal' TERM INT

# Wait for the stream parser to finish.  It exits when it sees a
# "result" event (success, rc=0) or EOF without one (failure, rc=1).
wait "$stream_pid" 2>/dev/null && stream_rc=0 || stream_rc=$?

# Stream parser is done — clean up claude.
kill "$claude_pid" 2>/dev/null || true
wait "$claude_pid" 2>/dev/null && claude_rc=0 || claude_rc=$?

# Parser failure should still fail the container immediately.
if [[ "$stream_rc" -ne 0 ]]; then
    exit "$stream_rc"
fi

# Treat normal exit and intentional SIGTERM (143 = 128+15) as success;
# propagate anything else (e.g. claude exiting 1 or 2).
if [[ "$claude_rc" -eq 0 || "$claude_rc" -eq 143 ]]; then
    exit 0
fi

exit "$claude_rc"
