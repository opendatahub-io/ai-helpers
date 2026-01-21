---
description: "Smart commit squashing with intelligent message combination"
argument-hint: "[count_or_sha] [style]"
---

## Name
git:merge

## Synopsis
```
/git:merge [count_or_sha] [style]
```

## Description

Intelligently squashes commits using soft reset with automatic commit message combination and tone detection. Consolidates multiple commits into a single cohesive commit with a synthesized message.

## Usage
- `/git:merge` - Merge last 2 commits with auto-style detection
- `/git:merge 1` - Merge last 2 commits (explicit)
- `/git:merge N` - Merge last N+1 commits (top + N previous)
- `/git:merge SHA` - Merge from HEAD back to and including specified SHA
- `/git:merge N dev` - Force verbose development style for combined message
- `/git:merge SHA final` - Force concise final style for combined message

## Merge Modes

### Count-Based Merging
```bash
/git:merge 3         # Merges: HEAD + 3 previous commits (4 total)
/git:merge 1         # Merges: HEAD + 1 previous commit (2 total)
/git:merge 3 dev     # Merge 4 commits with verbose style
/git:merge 1 final   # Merge 2 commits with concise style
```

### SHA-Based Merging
```bash
/git:merge abc1234        # Merges: HEAD back to abc1234 (inclusive)
/git:merge abc123         # Short SHA also supported
/git:merge abc1234 dev    # Merge to SHA with verbose style
/git:merge abc123 final   # Merge to SHA with concise style
```

## Style Control

### Tone Keywords
- **Verbose triggers**: `dev`, `wip`, `verbose`, `detailed`
- **Concise triggers**: `final`, `concise`, `clean`, `prod`

### Style Detection Priority
1. **Explicit style argument**: Always takes precedence
2. **Commit message analysis**: Examine predominant style in merge range
3. **Auto-detection**: Based on change scope and context
4. **Default**: Verbose development style when uncertain

## Implementation

### 1. Validate Range
- **Count mode**: Verify sufficient commit history exists
- **SHA mode**: Confirm SHA exists and is reachable from HEAD
- **Safety check**: Prevent merging past main branch divergence point

### 2. Analyze Commit Messages
The AI examines all commits in the merge range:
- **Message content**: Detect development vs final style commits
- **Change scope**: Assess if changes are related or disparate
- **Tone consistency**: Identify predominant commit style pattern
- **Context preservation**: Extract key information from verbose commits

### 3. Generate Combined Message

#### Style Detection Logic
- **Explicit style**: Honor `dev`/`final` argument when provided
- **All verbose commits**: Preserve detailed context in combined message
- **All concise commits**: Create concise combined message
- **Mixed styles**: Use most recent commit's style as template
- **Auto-detection**: Analyze change scope and relationships

#### Message Combination Patterns

**Verbose Output (Development-style commits)**:
```
Combined implementation of [feature area]

Detailed context:
- Key architectural decisions from all commits
- Consolidated file changes and reasoning
- Combined blockers and solutions
- Integrated testing approaches
- Next steps synthesis

Co-authored-by: Claude <noreply@anthropic.com>
```

**Concise Output (Final-style commits)**:
```
Implement [feature area]

- Combined key change 1
- Combined key change 2
- Combined key change 3

Co-authored-by: Claude <noreply@anthropic.com>
```

### 4. Execute Merge
```bash
# Soft reset to target commit
git reset --soft <target-commit>^

# Create new combined commit
git commit -m "Generated combined message"
```

## Smart Message Synthesis

### Information Extraction
- **Deduplicate**: Remove redundant information across commits
- **Prioritize**: Emphasize most significant changes and decisions
- **Contextualize**: Maintain architectural reasoning and blockers
- **Synthesize**: Combine related changes into logical groupings

### Tone Preservation
- **Development tone**: Maintain detailed context and reasoning
- **Final tone**: Focus on completed functionality and key changes
- **Mixed commits**: Adapt to predominant style or most recent commit intent

## Safety Features

### Pre-merge Validation
- **History check**: Ensure commits are consecutive and reachable
- **Branch verification**: Confirm not merging across branch boundaries
- **Backup suggestion**: Recommend creating backup branch for complex merges

### Error Handling
- **Invalid SHA**: Clear error message with suggestions
- **Insufficient history**: Graceful failure with available commit count
- **Merge conflicts**: Guide user through resolution process

## Examples

### Count-based Merge
```bash
git log --oneline -4
# abc1234 Fix authentication bug
# def5678 WIP: implement OAuth flow - token handling complete
# ghi9012 Add user registration endpoint
# jkl3456 Update database schema

/git:merge 2         # Auto-detect style (likely verbose due to WIP commit)
/git:merge 2 final   # Force concise final style for cleanup
/git:merge 2 dev     # Force verbose style to preserve context
```

### SHA-based Merge
```bash
git log --oneline -4
# abc1234 Final authentication implementation
# def5678 Fix token refresh logic
# ghi9012 Add OAuth configuration
# jkl3456 Previous unrelated commit

/git:merge ghi9012 final   # Merge 3 commits with clean final style
/git:merge ghi9012 dev     # Merge 3 commits preserving detailed context
```

### Style Transformation Examples

#### Development to Final Cleanup
```bash
# Before: Multiple verbose WIP commits
git log --oneline -3
# abc1234 WIP: OAuth complete - debugging refresh tokens, session handling works
# def5678 WIP: add token validation - expiration checks done, need cleanup
# ghi9012 WIP: user auth foundation - basic flow working, error handling pending

/git:merge 2 final
# Result: Clean concise commit ready for production
```

#### Context Preservation
```bash
# Before: Terse commits that need context
git log --oneline -3
# abc1234 Fix bug
# def5678 Update auth
# ghi9012 Add validation

/git:merge 2 dev
# Result: Detailed explanation of what was actually fixed/changed
```

## Integration with Git Guidelines

### Follows Framework Patterns
- **Non-interactive**: Uses `git reset --soft` instead of interactive rebase
- **Message synthesis**: Applies commit style decision matrix
- **Co-authorship**: Maintains proper attribution
- **Safety first**: Validates before executing destructive operations

### Complements /git:commit Command
- **Development phase**: Use `/git:commit dev` for detailed WIP commits
- **Cleanup phase**: Use `/git:merge N` to consolidate related commits
- **Final phase**: Use `/git:commit final` for clean final commits
- **History management**: Strategic combination of both commands
