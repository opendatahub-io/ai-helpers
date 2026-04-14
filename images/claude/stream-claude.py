#!/usr/bin/env python3
"""Parse Claude Code stream-json output into a human-readable CI log."""

import argparse
import atexit
import json
import re
import sys
import time

parser = argparse.ArgumentParser(description="Parse Claude Code stream-json output")
parser.add_argument(
    "--wrap",
    type=int,
    default=0,
    metavar="COLS",
    help="Word-wrap output at COLS columns (0 = no wrapping)",
)
parser.add_argument(
    "--no-color",
    action="store_true",
    help="Disable ANSI color codes in output",
)
parser.add_argument(
    "--log-file",
    type=str,
    default="",
    help="Write plain-text (no ANSI) output to this file",
)
args = parser.parse_args()

# ANSI colors (GitLab CI supports these)
if args.no_color:
    THINK_COLOR = TOOL_COLOR = CLAUDE_COLOR = RED = YELLOW = RESET = ""
else:
    THINK_COLOR = "\033[3;31m"  # italic red
    TOOL_COLOR = "\033[1;90m"  # bold gray
    CLAUDE_COLOR = ""  # normal
    RED = "\033[31m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def _safe(text):
    """Strip ANSI escapes, control characters, and CI workflow commands."""
    text = str(text)
    text = _ANSI_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    if text.startswith("::"):
        text = f" {text}"
    return text


log_file = open(args.log_file, "w") if args.log_file else None
if log_file:
    atexit.register(log_file.close)

active_block = None  # "text", "thinking", or None
_saw_result = False
tool_name = None
tool_json_parts = []
_line_buf = ""
_total_input_tokens = 0
_total_output_tokens = 0
_total_cache_read = 0
_total_cache_write = 0
_last_emitted_total = 0
_last_emitted_time = 0.0


def _log(text):
    """Write plain text to the log file (if configured)."""
    if log_file:
        log_file.write(text)
        log_file.flush()


def emit(text):
    """Buffer text and flush complete lines."""
    global _line_buf
    _line_buf += text
    while "\n" in _line_buf:
        line, _line_buf = _line_buf.split("\n", 1)
        if args.wrap and len(line) > args.wrap:
            # Word-boundary wrap
            wrapped = ""
            col = 0
            for word in line.split(" "):
                if col + len(word) > args.wrap and col > 0:
                    wrapped += "\n"
                    col = 0
                if col > 0:
                    wrapped += " "
                    col += 1
                wrapped += word
                col += len(word)
            print(wrapped, flush=True)
            _log(wrapped + "\n")
        else:
            print(line, flush=True)
            _log(line + "\n")


def flush_emit():
    """Flush any remaining buffered text."""
    global _line_buf
    if _line_buf:
        print(_line_buf, flush=True)
        _log(_line_buf + "\n")
        _line_buf = ""


def _print(text, end="\n"):
    """Print colored text to stdout and plain text to the log file."""
    print(text, end=end, flush=True)
    if log_file:
        plain = _ANSI_RE.sub("", text)
        log_file.write(plain + end)
        log_file.flush()


def _format_tool(name, params):
    """Return a compact one-line summary for a tool call."""
    if name == "Bash":
        cmd = params.get("command", "")
        desc = params.get("description", "")
        return f"$ {cmd}" + (f"  # {desc}" if desc else "")
    if name == "Read":
        path = params.get("file_path", "")
        parts = [path]
        if "offset" in params:
            parts.append(f"L{params['offset']}")
        if "limit" in params:
            parts.append(f"+{params['limit']}")
        return " ".join(parts)
    if name == "Write":
        return params.get("file_path", "")
    if name == "Edit":
        path = params.get("file_path", "")
        old = params.get("old_string", "")
        preview = old.split("\n")[0][:60]
        if len(old) > len(preview):
            preview += "..."
        return f"{path}: {preview}"
    if name == "Glob":
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        return f"{pattern} in {path}"
    if name == "Grep":
        pattern = params.get("pattern", "")
        path = params.get("path", ".")
        return f"/{pattern}/ in {path}"
    if name == "Agent":
        desc = params.get("description", "")
        agent_type = params.get("subagent_type", "")
        return f"[{agent_type}] {desc}" if agent_type else desc
    if name == "Skill":
        skill = params.get("skill", "")
        skill_args = params.get("args", "")
        return f"/{skill} {skill_args}".strip()
    if name == "TaskGet":
        return params.get("task_id", "")
    # Generic fallback: key=value pairs on one line
    return ", ".join(f"{k}={v}" for k, v in params.items())


def end_block():
    global active_block, tool_name, tool_json_parts
    if active_block in ("text", "thinking"):
        flush_emit()
        sys.stdout.write(RESET + "\n")
        _log("\n")
        active_block = None
    if tool_name:
        tool_json = "".join(tool_json_parts)
        try:
            parsed = json.loads(tool_json)
        except (json.JSONDecodeError, ValueError):
            parsed = None

        summary = _safe(_format_tool(tool_name, parsed)) if parsed else None

        if summary:
            icon = "\U0001f916" if tool_name == "Agent" else "\U0001f527"
            _print(f"  {TOOL_COLOR}{icon} {tool_name} {summary}{RESET}")
        else:
            _print(f"  {TOOL_COLOR}\U0001f527 {tool_name}{RESET}")
            if parsed:
                formatted = json.dumps(parsed, indent=2)
                for fmtline in formatted.split("\n"):
                    _print(f"    {TOOL_COLOR}{fmtline}{RESET}")
        tool_name = None
        tool_json_parts = []


while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        msg = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue

    msg_type = msg.get("type")

    # System events (retries, etc.)
    if msg_type == "system":
        subtype = msg.get("subtype", "")
        if subtype == "api_retry":
            attempt = msg.get("attempt", "?")
            max_retries = msg.get("max_retries", "?")
            delay = msg.get("retry_delay_ms", "?")
            error = _safe(msg.get("error", "unknown"))
            _print(
                f"{YELLOW}\U0001f504 Retry {attempt}/{max_retries}{RESET} "
                f"{error} \u2014 retrying in {delay}ms",
            )
        elif subtype == "compact_boundary":
            meta = msg.get("compact_metadata", {})
            trigger = meta.get("trigger", "?")
            pre_tokens = meta.get("pre_tokens", "?")
            _print(
                f"{YELLOW}\U0001f4e6 Context compacted ({trigger}) pre_tokens={pre_tokens}{RESET}",
            )
        elif subtype == "hook_started":
            hook_name = _safe(msg.get("hook_name", "?"))
            _print(
                f"{YELLOW}\U0001fa9d Hook started: {hook_name}{RESET}",
            )
        elif subtype == "hook_response":
            hook_name = _safe(msg.get("hook_name", "?"))
            exit_code = msg.get("exit_code", "?")
            outcome = _safe(msg.get("outcome", "?"))
            stdout = _safe(msg.get("stdout", "").strip())
            stderr = _safe(msg.get("stderr", "").strip())
            _print(
                f"{YELLOW}\U0001fa9d Hook {hook_name}: {outcome} (rc={exit_code}){RESET}",
            )
            if stdout:
                for out_line in stdout.split("\n"):
                    _print(f"  {YELLOW}{out_line}{RESET}")
            if stderr:
                for err_line in stderr.split("\n"):
                    _print(f"  {RED}{err_line}{RESET}")
        continue

    if msg_type == "result":
        _saw_result = True
        end_block()
        break

    if msg_type != "stream_event":
        continue

    event = msg.get("event", {})
    event_type = event.get("type")

    # Content block start
    if event_type == "content_block_start":
        block = event.get("content_block", {})
        block_type = block.get("type")
        if block_type == "text":
            print(f"{CLAUDE_COLOR}\U0001f4ac Claude ", end="", flush=True)
            _log("\U0001f4ac Claude ")
            active_block = "text"
        elif block_type == "thinking":
            print(f"{THINK_COLOR}\U0001f9e0 Thinking ", end="", flush=True)
            _log("\U0001f9e0 Thinking ")
            active_block = "thinking"
        elif block_type in ("tool_use", "server_tool_use"):
            tool_name = block.get("name", "unknown")
            tool_json_parts = []

    # Content block deltas
    elif event_type == "content_block_delta":
        delta = event.get("delta", {})
        delta_type = delta.get("type")
        if delta_type == "text_delta":
            emit(_safe(delta.get("text", "")))
        elif delta_type == "thinking_delta":
            emit(_safe(delta.get("thinking", "")))
        elif delta_type == "input_json_delta":
            tool_json_parts.append(delta.get("partial_json", ""))

    # Content block stop
    elif event_type == "content_block_stop":
        end_block()

    # Message start -- carries cumulative input token counts
    elif event_type == "message_start":
        usage = event.get("message", {}).get("usage", {})
        _total_input_tokens = usage.get("input_tokens", 0)
        _total_cache_read = usage.get("cache_read_input_tokens", 0)
        _total_cache_write = usage.get("cache_creation_input_tokens", 0)

    # Message delta -- carries cumulative output token count
    elif event_type == "message_delta":
        usage = event.get("usage", {})
        out = usage.get("output_tokens", 0)
        if out > 0:
            _total_output_tokens = out
            total = (
                _total_input_tokens + _total_output_tokens + _total_cache_read + _total_cache_write
            )
            # Emit every 5k tokens to avoid noise
            if total - _last_emitted_total >= 5_000 or _last_emitted_total == 0:
                now = time.monotonic()
                rate = 0.0
                if _last_emitted_time > 0:
                    dt = now - _last_emitted_time
                    dv = total - _last_emitted_total
                    if dt > 0:
                        rate = dv / dt
                rate_str = f" rate={rate:.0f}/s" if rate > 0 else ""
                _last_emitted_total = total
                _last_emitted_time = now
                _print(
                    f"{TOOL_COLOR}  \U0001f4ca TOKENS in={_total_input_tokens}"
                    f" out={_total_output_tokens}"
                    f" cache_r={_total_cache_read}"
                    f" cache_w={_total_cache_write}"
                    f" total={total}{rate_str}{RESET}",
                )

    # Errors
    elif event_type == "error":
        error = event.get("error", {})
        error_type = _safe(error.get("type", "unknown"))
        error_msg = _safe(error.get("message", ""))
        _print(
            f"{RED}\u274c Error: {error_type}: {error_msg}{RESET}",
        )

print()
sys.exit(0 if _saw_result else 1)
