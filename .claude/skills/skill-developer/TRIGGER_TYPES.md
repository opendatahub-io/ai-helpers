# Trigger Types - Complete Guide

Complete reference for configuring skill triggers in Claude Code's skill auto-activation system.

## Table of Contents

- [Keyword Triggers (Explicit)](#keyword-triggers-explicit)
- [Intent Pattern Triggers (Implicit)](#intent-pattern-triggers-implicit)
- [File Path Triggers](#file-path-triggers)
- [Content Pattern Triggers](#content-pattern-triggers)
- [Best Practices Summary](#best-practices-summary)

---

## Keyword Triggers (Explicit)

### How It Works

Case-insensitive substring matching in user's prompt.

### Use For

Topic-based activation where user explicitly mentions the subject.

### Configuration

```json
"promptTriggers": {
  "keywords": ["layout", "grid", "toolbar", "submission"]
}
```

### Example

- User prompt: "how does the **layout** system work?"
- Matches: "layout" keyword
- Activates: `project-catalog-developer`

### Best Practices

- Use specific, unambiguous terms
- Include common variations ("layout", "layout system", "grid layout")
- Avoid overly generic words ("system", "work", "create")
- Test with real prompts

---

## Intent Pattern Triggers (Implicit)

### How It Works

Regex pattern matching to detect user's intent even when they don't mention the topic explicitly.

### Use For

Action-based activation where user describes what they want to do rather than the specific topic.

### Configuration

```json
"promptTriggers": {
  "intentPatterns": [
    "(create|add|implement).*?(feature|endpoint)",
    "(how does|explain).*?(layout|workflow)"
  ]
}
```

### Examples

**Database Work:**
- User prompt: "add user tracking feature"
- Matches: `(add).*?(feature)`
- Activates: `database-verification`, `error-tracking`

**Module Creation:**
- User prompt: "create a database module"
- Matches: `(create).*?(module)` (if module in pattern)
- Activates: `python-dev-guidelines`

### Best Practices

- Capture common action verbs: `(create|add|modify|build|implement)`
- Include domain-specific nouns: `(feature|endpoint|component|workflow)`
- Use non-greedy matching: `.*?` instead of `.*`
- Test patterns thoroughly with regex tester (https://regex101.com/)
- Don't make patterns too broad (causes false positives)
- Don't make patterns too specific (causes false negatives)

### Common Pattern Examples

```regex
# Database Work
(add|create|implement).*?(user|login|auth|feature)

# Explanations
(how does|explain|what is|describe).*?

# Python Development
(create|add|make|build).*?(module|class|function|package)

# Error Handling
(fix|handle|catch|debug).*?(error|exception|bug)

# Workflow Operations
(create|add|modify).*?(workflow|step|branch|condition)
```

---

## File Path Triggers

### How It Works

Glob pattern matching against the file path being edited.

### Use For

Domain/area-specific activation based on file location in the project.

### Configuration

```json
"fileTriggers": {
  "pathPatterns": [
    "src/**/*.py",
    "lib/**/*.cpp"
  ],
  "pathExclusions": [
    "**/*_test.py",
    "**/test_*.py"
  ]
}
```

### Glob Pattern Syntax

- `**` = Any number of directories (including zero)
- `*` = Any characters within a directory name
- Examples:
  - `src/**/*.py` = All .py files in src and subdirs
  - `**/schema.sql` = schema.sql anywhere in project
  - `lib/**/*.cpp` = All .cpp files in lib subdirs

### Example

- File being edited: `src/components/dashboard.py`
- Matches: `src/**/*.py`
- Activates: `python-dev-guidelines`

### Best Practices

- Be specific to avoid false positives
- Use exclusions for test files: `**/*_test.py`
- Consider subdirectory structure
- Test patterns with actual file paths
- Use narrower patterns when possible: `src/services/**` not `src/**`

### Common Path Patterns

```glob
# Python Source
src/**/*.py                 # All Python source files
lib/**/*.py                 # Library files
app/**/*.py                 # Application files

# C/C++ Source
src/**/*.cpp                # C++ source files
src/**/*.c                  # C source files
include/**/*.h              # C header files
include/**/*.hpp            # C++ header files

# CUDA Source
**/*.cu                     # CUDA source files
**/*.cuh                    # CUDA header files
kernels/**/*.cu             # CUDA kernels

# Database/Config
**/schema.sql               # SQL schema files
**/migrations/**/*.sql      # Migration files
**/*.yaml                   # YAML config files
**/*.json                   # JSON config files

# Test Exclusions
**/*_test.py                # Python tests (_test suffix)
**/test_*.py                # Python tests (test_ prefix)
**/*.test.cpp               # C++ tests
**/tests/**                 # Test directories
```

---

## Content Pattern Triggers

### How It Works

Regex pattern matching against the file's actual content (what's inside the file).

### Use For

Technology-specific activation based on what the code imports or uses (SQLAlchemy, CUDA kernels, specific libraries).

### Configuration

```json
"fileTriggers": {
  "contentPatterns": [
    "import.*sqlalchemy",
    "from.*database import",
    "session\\.(query|add)",
    "__global__.*void"
  ]
}
```

### Examples

**Database Detection:**
- File contains: `import sqlalchemy`
- Matches: `import.*sqlalchemy`
- Activates: `database-verification`

**CUDA Kernel Detection:**
- File contains: `__global__ void myKernel()`
- Matches: `__global__.*void`
- Activates: `cuda-development`

### Best Practices

- Match imports: `import.*sqlalchemy` (case-insensitive)
- Escape special regex chars: `session\\.query` not `session.query`
- Patterns use case-insensitive flag
- Test against real file content
- Make patterns specific enough to avoid false matches

### Common Content Patterns

```regex
# Python Database
import.*sqlalchemy              # SQLAlchemy imports
from.*database import           # Database imports
session\.(query|add|commit)     # Database session operations

# Python Imports
^import\s+\w+                   # Standard imports
^from\s+\w+\s+import            # From imports
__init__\.py                    # Package initialization

# Error Handling
try:                            # Try blocks
except\s+\w+:                   # Except blocks
raise\s+\w+Error                # Raise statements

# C/C++ Patterns
#include\s*<.*>                 # System includes
#include\s*".*"                 # Local includes
extern\s+"C"                    # C linkage
template\s*<                    # Template definitions

# CUDA Patterns
__global__\s+void               # CUDA kernels
__device__\s+                   # Device functions
cudaMalloc|cudaMemcpy           # CUDA API calls
```

---

## Best Practices Summary

### DO:
✅ Use specific, unambiguous keywords
✅ Test all patterns with real examples
✅ Include common variations
✅ Use non-greedy regex: `.*?`
✅ Escape special characters in content patterns
✅ Add exclusions for test files
✅ Make file path patterns narrow and specific

### DON'T:
❌ Use overly generic keywords ("system", "work")
❌ Make intent patterns too broad (false positives)
❌ Make patterns too specific (false negatives)
❌ Forget to test with regex tester (https://regex101.com/)
❌ Use greedy regex: `.*` instead of `.*?`
❌ Match too broadly in file paths

### Testing Your Triggers

**Test keyword/intent triggers:**
```bash
echo '{"session_id":"test","prompt":"your test prompt"}' | \
  python3 .claude/hooks/skill_activation_prompt.py
```

**Test file path/content triggers:**
```bash
cat <<'EOF' | python3 .claude/hooks/pre-tool-use.py
{
  "session_id": "test",
  "tool_name": "Edit",
  "tool_input": {"file_path": "/path/to/test/file.py"}
}
EOF
```

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main skill guide
- [SKILL_RULES_REFERENCE.md](SKILL_RULES_REFERENCE.md) - Complete skill-rules.json schema
- [PATTERNS_LIBRARY.md](PATTERNS_LIBRARY.md) - Ready-to-use pattern library