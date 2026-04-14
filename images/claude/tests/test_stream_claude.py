"""Smoke tests for stream-claude.py.

Each test feeds a known JSON fixture into the parser via subprocess and
checks that the output contains the expected human-readable lines.
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "stream-claude.py")


def _run(events, extra_args=None):
    """Feed *events* (list of dicts) into stream-claude.py and return (stdout, returncode)."""
    input_data = "\n".join(json.dumps(e) for e in events) + "\n"
    cmd = [sys.executable, "-u", SCRIPT, "--no-color"] + (extra_args or [])
    proc = subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return proc.stdout, proc.returncode


# ---------------------------------------------------------------------------
# Fixtures — minimal JSON events that exercise each code path
# ---------------------------------------------------------------------------


def _text_block(text):
    """Return start / delta / stop events for a text content block."""
    return [
        {
            "type": "stream_event",
            "event": {"type": "content_block_start", "content_block": {"type": "text"}},
        },
        {
            "type": "stream_event",
            "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": text}},
        },
        {"type": "stream_event", "event": {"type": "content_block_stop"}},
    ]


def _thinking_block(text):
    return [
        {
            "type": "stream_event",
            "event": {"type": "content_block_start", "content_block": {"type": "thinking"}},
        },
        {
            "type": "stream_event",
            "event": {
                "type": "content_block_delta",
                "delta": {"type": "thinking_delta", "thinking": text},
            },
        },
        {"type": "stream_event", "event": {"type": "content_block_stop"}},
    ]


def _tool_block(name, params):
    partial = json.dumps(params)
    return [
        {
            "type": "stream_event",
            "event": {
                "type": "content_block_start",
                "content_block": {"type": "tool_use", "name": name},
            },
        },
        {
            "type": "stream_event",
            "event": {
                "type": "content_block_delta",
                "delta": {"type": "input_json_delta", "partial_json": partial},
            },
        },
        {"type": "stream_event", "event": {"type": "content_block_stop"}},
    ]


RESULT_EVENT = {"type": "result"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExitCode:
    def test_exits_0_on_result(self):
        events = _text_block("hello\n") + [RESULT_EVENT]
        _, rc = _run(events)
        assert rc == 0

    def test_exits_1_on_eof_without_result(self):
        events = _text_block("hello\n")
        _, rc = _run(events)
        assert rc == 1


class TestTextOutput:
    def test_text_block_rendered(self):
        events = _text_block("Hello world\n") + [RESULT_EVENT]
        out, _ = _run(events)
        assert "Claude" in out
        assert "Hello world" in out

    def test_thinking_block_rendered(self):
        events = _thinking_block("Let me think...\n") + [RESULT_EVENT]
        out, _ = _run(events)
        assert "Thinking" in out
        assert "Let me think..." in out


class TestToolFormatting:
    def test_bash_tool(self):
        events = _tool_block("Bash", {"command": "ls -la", "description": "List files"}) + [
            RESULT_EVENT
        ]
        out, _ = _run(events)
        assert "$ ls -la" in out
        assert "# List files" in out

    def test_read_tool(self):
        events = _tool_block("Read", {"file_path": "/tmp/foo.py"}) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "/tmp/foo.py" in out

    def test_edit_tool(self):
        events = _tool_block(
            "Edit", {"file_path": "/tmp/foo.py", "old_string": "old", "new_string": "new"}
        ) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "/tmp/foo.py" in out
        assert "old" in out

    def test_grep_tool(self):
        events = _tool_block("Grep", {"pattern": "TODO", "path": "src/"}) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "/TODO/" in out
        assert "src/" in out

    def test_glob_tool(self):
        events = _tool_block("Glob", {"pattern": "**/*.py", "path": "."}) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "**/*.py" in out

    def test_write_tool(self):
        events = _tool_block("Write", {"file_path": "/tmp/new.py"}) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "/tmp/new.py" in out

    def test_agent_tool(self):
        events = _tool_block(
            "Agent", {"description": "Search codebase", "subagent_type": "Explore"}
        ) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "[Explore]" in out
        assert "Search codebase" in out

    def test_skill_tool(self):
        events = _tool_block("Skill", {"skill": "commit", "args": "-m 'fix'"}) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "/commit" in out

    def test_unknown_tool_shows_params(self):
        events = _tool_block("CustomTool", {"key": "value"}) + [RESULT_EVENT]
        out, _ = _run(events)
        assert "CustomTool" in out
        assert "key=value" in out


class TestSystemEvents:
    def test_api_retry(self):
        events = (
            [
                {
                    "type": "system",
                    "subtype": "api_retry",
                    "attempt": 1,
                    "max_retries": 3,
                    "retry_delay_ms": 1000,
                    "error": "rate_limit",
                },
            ]
            + _text_block("ok\n")
            + [RESULT_EVENT]
        )
        out, _ = _run(events)
        assert "Retry 1/3" in out
        assert "rate_limit" in out

    def test_compact_boundary(self):
        events = [
            {
                "type": "system",
                "subtype": "compact_boundary",
                "compact_metadata": {"trigger": "auto", "pre_tokens": 50000},
            },
        ] + [RESULT_EVENT]
        out, _ = _run(events)
        assert "compacted" in out
        assert "auto" in out

    def test_hook_events(self):
        events = [
            {"type": "system", "subtype": "hook_started", "hook_name": "pre-commit"},
            {
                "type": "system",
                "subtype": "hook_response",
                "hook_name": "pre-commit",
                "exit_code": 0,
                "outcome": "success",
                "stdout": "ok",
                "stderr": "",
            },
        ] + [RESULT_EVENT]
        out, _ = _run(events)
        assert "Hook started: pre-commit" in out
        assert "success" in out


class TestErrorEvent:
    def test_error_rendered(self):
        events = [
            {
                "type": "stream_event",
                "event": {
                    "type": "error",
                    "error": {"type": "overloaded", "message": "server busy"},
                },
            },
        ]
        out, _ = _run(events)
        assert "overloaded" in out
        assert "server busy" in out


class TestLogFile:
    def test_log_file_written_without_ansi(self):
        events = _text_block("logged output\n") + [RESULT_EVENT]
        with tempfile.NamedTemporaryFile(mode="r", suffix=".log", delete=False) as f:
            log_path = f.name
        try:
            _run(events, extra_args=["--log-file", log_path])
            with open(log_path) as f:
                content = f.read()
            assert "logged output" in content
            assert "\033[" not in content
        finally:
            os.unlink(log_path)


class TestMalformedInput:
    def test_invalid_json_skipped(self):
        events = _text_block("valid\n") + [RESULT_EVENT]
        # Inject garbage between valid events
        input_lines = []
        for e in events[:1]:
            input_lines.append(json.dumps(e))
        input_lines.append("this is not json {{{")
        for e in events[1:]:
            input_lines.append(json.dumps(e))
        input_data = "\n".join(input_lines) + "\n"

        cmd = [sys.executable, "-u", SCRIPT, "--no-color"]
        proc = subprocess.run(cmd, input=input_data, capture_output=True, text=True, timeout=10)
        assert proc.returncode == 0
        assert "valid" in proc.stdout


class TestTokenStats:
    def test_token_stats_emitted(self):
        events = [
            {
                "type": "stream_event",
                "event": {
                    "type": "message_start",
                    "message": {
                        "usage": {
                            "input_tokens": 5000,
                            "cache_read_input_tokens": 1000,
                            "cache_creation_input_tokens": 500,
                        }
                    },
                },
            },
            {
                "type": "stream_event",
                "event": {"type": "message_delta", "usage": {"output_tokens": 200}},
            },
        ] + [RESULT_EVENT]
        out, _ = _run(events)
        assert "TOKENS" in out
        assert "in=5000" in out
        assert "out=200" in out
