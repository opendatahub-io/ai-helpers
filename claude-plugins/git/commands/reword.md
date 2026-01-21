---
description: "Smart commit message rewording with style transformation"
argument-hint: "[sha] [style_or_message]"
---

## Name
git:reword

## Synopsis
```
/git:reword [sha] [style_or_message]
```

## Description

Intelligently rewrites commit messages with style transformation and tone adjustment capabilities. Can transform verbose development commits into clean final messages or add context to terse commits.

## Usage
- `/git:reword SHA "New message"` - Reword with specific message
- `/git:reword SHA` - AI-assisted reword with auto-style detection
- `/git:reword SHA dev` - Transform to verbose development style
- `/git:reword SHA final` - Transform to concise final style

## Style Transformation

### Tone Keywords
- **Verbose triggers**: `dev`, `wip`, `verbose`, `detailed`
- **Concise triggers**: `final`, `concise`, `clean`, `prod`

### Smart Detection
When no style specified, AI analyzes:
- **Current message style**: Detect existing verbose vs concise pattern
- **Commit content**: Scope and complexity of changes
- **Position in history**: Recent vs older commits
- **Context clues**: File types and change patterns

## Implementation

### 1. Validate Commit
```bash
# Verify SHA exists and is reachable
git rev-parse --verify <sha>
git merge-base --is-ancestor <sha> HEAD
```

### 2. Analyze Current Message
Extract and analyze:
- **Current style**: Verbose development vs concise final
- **Content elements**: What information is present
- **Context quality**: How much detail exists
- **Transformation needs**: What style should result be

### 3. Message Transformation

#### To Verbose Style (dev/wip)
```
Original: "Fix authentication bug"

Transformed: "Fix authentication token validation bug

Detailed context:
- Token expiration validation was missing null checks
- Added proper error handling for expired tokens
- Updated authentication middleware to handle edge cases
- Fixed session cleanup on token invalidation

Co-authored-by: Claude <noreply@anthropic.com>"
```

#### To Concise Style (final/clean)
```
Original: "WIP: implement OAuth flow - token handling complete, session management in progress, need to debug refresh logic"

Transformed: "Implement OAuth authentication flow

- Add token handling and validation
- Implement session management
- Fix token refresh logic

Co-authored-by: Claude <noreply@anthropic.com>"
```

### 4. Execute Reword

#### Using Git Alias (Preferred)
```bash
git reword <sha> "New message here"
```

#### Fallback Method
```bash
GIT_SEQUENCE_EDITOR="sed -i '' 1s/^pick/reword/" \
GIT_EDITOR="printf \"%s\n\" \"new message here\" >" \
git rebase -i <commit-hash>^
```

## Style Transformation Logic

### Content Analysis
The AI examines the commit to understand:
- **File changes**: What was actually modified
- **Change scope**: Small fix vs large feature
- **Technical complexity**: Simple update vs architectural change
- **Context availability**: How much can be inferred vs needs detail

### Message Enhancement Patterns

#### Verbose Enhancement
- **Expand reasoning**: Why changes were made
- **Add context**: Blockers encountered and solutions
- **Detail approach**: Technical decisions and alternatives
- **Include next steps**: Follow-up work or considerations

#### Concise Enhancement
- **Distill essence**: Core functionality delivered
- **Bullet key changes**: Most important modifications
- **Remove verbosity**: Strip implementation details
- **Focus on value**: What the commit accomplishes

## Examples

### Development Cleanup
```bash
# Convert old verbose commits to clean final style
/git:reword abc1234 final
/git:reword def5678 final
/git:reword ghi9012 final
```

### Adding Context
```bash
# Add detail to cryptic commit messages
/git:reword abc1234 dev
# "." becomes detailed explanation of changes
```

### Batch Style Conversion
```bash
# Multiple commits can be reworded with consistent style
git log --oneline -5  # Review recent commits
/git:reword <sha1> final
/git:reword <sha2> final
/git:reword <sha3> final
```

### Custom Message
```bash
# Provide specific new message
/git:reword abc1234 "Refactor authentication module for better testability"
```

## Safety Features
- **Validation**: Confirms SHA exists and is reachable before reword
- **Non-interactive**: Uses reliable non-interactive rebase methods
- **Backup suggestion**: Recommends creating backup branch for complex operations
- **Style preservation**: When no style specified, preserves original intent

## Git Alias Integration
Automatically detects and uses `git reword` alias when available:
```bash
reword = "!f() {\n  GIT_SEQUENCE_EDITOR=\"sed -i '' 1s/^pick/reword/\" GIT_EDITOR=\"printf \\\"%s\\n\\\" \\\"$2\\\" >\" git rebase -i \"$1^\";\n}; f"
```

Falls back to manual method when alias not configured.

## Integration with Other Commands

### Workflow with /git:commit and /git:merge
- **During development**: Use `/git:commit dev` for verbose WIP commits
- **Before PR**: Use `/git:reword SHA final` to clean up commit messages
- **Alternative**: Use `/git:merge N final` to squash and clean simultaneously
