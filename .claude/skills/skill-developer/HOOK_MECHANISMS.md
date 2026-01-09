# Hook Mechanisms - Deep Dive

Technical deep dive into how the UserPromptSubmit hook works.

## Table of Contents

- [UserPromptSubmit Hook Flow](#userpromptsubmit-hook-flow)
- [Exit Code Behavior (CRITICAL)](#exit-code-behavior-critical)
- [Session State Management](#session-state-management)
- [Performance Considerations](#performance-considerations)

---

## UserPromptSubmit Hook Flow

### Execution Sequence

```
User submits prompt
    ↓
.claude/settings.json registers hook
    ↓
skill_activation_prompt.py executes
    ↓
python3 skill_activation_prompt.py
    ↓
Hook reads stdin (JSON with prompt)
    ↓
Loads skill-rules.json
    ↓
Matches keywords + intent patterns
    ↓
Groups matches by priority (critical → high → medium → low)
    ↓
Outputs formatted message to stdout
    ↓
stdout becomes context for Claude (injected before prompt)
    ↓
Claude sees: [skill suggestion] + user's prompt
```

### Key Points

- **Exit code**: Always 0 (allow)
- **stdout**: → Claude's context (injected as system message)
- **Timing**: Runs BEFORE Claude processes prompt
- **Behavior**: Non-blocking, advisory only
- **Purpose**: Make Claude aware of relevant skills

### Input Format

```json
{
  "session_id": "abc-123",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/root/git/your-project",
  "permission_mode": "normal",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "how does the layout system work?"
}
```

### Output Format (to stdout)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SKILL ACTIVATION CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 RECOMMENDED SKILLS:
  → project-catalog-developer

ACTION: Use Skill tool BEFORE responding
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Claude sees this output as additional context before processing the user's prompt.

---

### Execution Sequence

```
Claude calls Edit/Write tool
    ↓
.claude/settings.json registers hook (matcher: Edit|Write)
    ↓
skill_activation_prompt.sh executes
    ↓
python skill_activation_prompt.py
    ↓
Hook reads stdin (JSON with tool_name, tool_input)
    ↓
Loads skill-rules.json
    ↓
Matches keywords + intent patterns
    ↓
Groups matches by priority (critical → high → medium → low)
    ↓
Outputs formatted message to stdout
    ↓
stdout becomes context for Claude (injected before prompt)
    ↓
Claude sees: [skill suggestion] + user's prompt
    
IF MATCHED AND NOT SKIPPED:
  Update session state (mark skill as enforced)
  Output block message to stderr
  Exit with code 2 (BLOCK)
ELSE:
  Exit with code 0 (ALLOW)
    ↓
IF BLOCKED:
  stderr → Claude sees message
  Edit/Write tool does NOT execute
  Claude must use skill and retry
IF ALLOWED:
  Tool executes normally
```

### Key Points

- **Exit code 2**: BLOCK (stderr → Claude)
- **Exit code 0**: ALLOW
- **Timing**: Runs BEFORE tool execution
- **Session tracking**: Prevents repeated blocks in same session
- **Fail open**: On errors, allows operation (don't break workflow)
- **Purpose**: Enforce critical guardrails

### Input Format

```json
{
  "session_id": "abc-123",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/root/git/your-project",
  "permission_mode": "normal",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/root/git/your-project/src/services/user.py",
    "old_string": "...",
    "new_string": "..."
  }
}
```

### Output Format (to stderr when blocked)

```
⚠️ BLOCKED - Database Operation Detected

📋 REQUIRED ACTION:
1. Use Skill tool: 'database-verification'
2. Verify ALL table and column names against schema
3. Check database structure with DESCRIBE commands
4. Then retry this edit

Reason: Prevent column name errors in Prisma queries
File: src/services/user.py

💡 TIP: Add '// @skip-validation' comment to skip future checks
```

Claude receives this message and understands it needs to use the skill before retrying the edit.

---

## Exit Code Behavior (CRITICAL)

### Exit Code Reference Table

| Exit Code | stdout | stderr | Tool Execution | Claude Sees |
|-----------|--------|--------|----------------|-------------|
| 0 (UserPromptSubmit) | → Context | → User only | N/A | stdout content |
| Other | → User only | → User only | Blocked | Nothing |


### Example Conversation Flow

```
User: "Add a new user service with Prisma"

Claude: "I'll create the user service..."
    [Attempts to Edit src/services/user.py]

Claude sees error, responds:
    "I need to verify the database schema first."
    [Uses Skill tool: database-verification]
    [Verifies column names]
    [Retries Edit - now allowed (session tracking)]
```

---

## Session State Management

### Purpose

Prevent repeated nagging in the same session - once Claude uses a skill, don't block again.

### State File Location

`.claude/hooks/state/skills-used-{session_id}.json`

### State File Structure

```json
{
  "skills_used": [
    "database-verification",
    "error-tracking"
  ],
  "files_verified": []
}
```

### How It Works

1. **First edit** of file with Prisma:
   - Hook blocks with exit code 2
   - Updates session state: adds "database-verification" to skills_used
   - Claude sees message, uses skill

2. **Second edit** (same session):
   - Hook checks session state
   - Finds "database-verification" in skills_used
   - Exits with code 0 (allow)
   - No message to Claude

3. **Different session**:
   - New session ID = new state file
   - Hook blocks again

### Limitation

The hook cannot detect when the skill is *actually* invoked - it just blocks once per session per skill. This means:

- If Claude doesn't use the skill but makes a different edit, it won't block again
- Trust that Claude follows the instruction
- Future enhancement: detect actual Skill tool usage

---

### Optimization Strategies

**Reduce patterns:**
- Use more specific patterns (fewer to check)
- Combine similar patterns where possible

**File path patterns:**
- More specific = fewer files to check
- Example: `form/src/services/**` better than `form/**`

**Content patterns:**
- Only add when truly necessary
- Simpler regex = faster matching

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main skill guide
- [SKILL_RULES_REFERENCE.md](SKILL_RULES_REFERENCE.md) - Configuration reference