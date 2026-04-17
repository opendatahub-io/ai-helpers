---
name: doc-gather
description: >
  Gather context for a Jira ticket or PR. Resolves ticket metadata,
  clones relevant repos, collects candidate files, runs filtering
  pipeline, and produces workspace/context-package.json.
argument-hint: "<JIRA-KEY|PR-URL>"
model: claude-sonnet-4-5
effort: high
---

# doc-gather

Gather context from Jira tickets, source repos, and documentation repos to produce a structured context package for downstream skills.

## Parse arguments

`$ARGUMENTS` contains either:
- A Jira ticket key (e.g., `RHOAIENG-55490`)
- A PR/MR URL (e.g., `https://github.com/org/repo/pull/123`)

Detect the input type:
- If it starts with `http` → PR URL
- Otherwise → Jira ticket key

## Step 1: Resolve ticket metadata

### For Jira tickets

Use the resolve script to fetch and structure ticket metadata:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/resolve-jira.sh <JIRA-KEY>
```

This returns JSON with: `key`, `summary`, `description`, `acceptance_criteria`, `fix_versions`, `components`, `linked_tickets`, `epic_key`, `status`, `issue_type`.

If the ticket has linked tickets that provide useful context (e.g., parent epic, related stories), resolve those too (up to 5 linked tickets):

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/resolve-jira.sh <LINKED-KEY>
```

### For PR URLs

Use `gh` CLI to extract PR metadata:

```bash
gh pr view <PR-URL> --json title,body,labels,files,headRefName
```

Extract the Jira key from the PR title or body (pattern: `[A-Z]+-\d+`), then resolve the Jira ticket using the resolve script as above.

## Step 2: Parse product configuration

Read the product configuration bundled with this skill:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/parse-product-config.py ${CLAUDE_SKILL_DIR}/configs/rhoai.yaml
```

From the config, determine:
1. **Context sources** — which repos to clone and where to find files
2. **Version mappings** — how to map Jira fixVersion to git branches
3. **Component resolver** — map Jira component names to repo slugs
4. **Docs conventions** — module prefixes, framework, attribute files

## Step 3: Resolve version to branches

For each fixVersion from the ticket:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/parse-product-config.py ${CLAUDE_SKILL_DIR}/configs/rhoai.yaml --resolve-version "<fixVersion>"
```

This determines which branch to checkout for each repo.

## Step 4: Resolve components to repos

For each component from the ticket:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/parse-product-config.py ${CLAUDE_SKILL_DIR}/configs/rhoai.yaml --resolve-component "<component-name>"
```

This identifies which source repos are relevant.

## Step 5: Clone and collect candidate files

For each context source in the product config, plus each resolved component repo:

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/gather-context.sh <repo-slug> <branch> <path-patterns...>
```

The branch is determined by:
1. Version resolution from Step 3 (if applicable)
2. The `branch_hint` from the context source declaration
3. Fallback to `main`

## Step 6: Run filtering pipeline

Assemble a JSON input for the filtering pipeline combining:
- All candidate files from Step 5
- Task context (ticket metadata as keywords, components, version)
- Source declarations from product config

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/context-filter.py <<< '<assembled-json>'
```

The pipeline runs six stages:
1. **Static inclusion** — mark always_include sources
2. **Version branch** — (already resolved in Step 3)
3. **Component affinity** — filter by component overlap
4. **Path relevance** — score by path patterns and keywords
5. **Keyword relevance** — BM25 scoring against ticket text
6. **Budget enforcement** — select top candidates within 100K token budget

## Step 7: Read file contents

Source the git utilities and read each selected candidate's content from the cloned repo:

```bash
source ${CLAUDE_SKILL_DIR}/scripts/git-utils.sh
git_file_content "workspace/repos/<repo-slug>" "<file-path>"
```

Attach content to each candidate entry.

## Step 8: Write context package

Write `workspace/context-package.json` with this structure:

```json
{
    "ticket": {
        "key": "RHOAIENG-55490",
        "summary": "...",
        "description": "...",
        "fix_versions": ["rhoai-2.18"],
        "components": ["Dashboard"],
        "linked_tickets": [],
        "epic_key": "",
        "status": "In Progress",
        "issue_type": "Story"
    },
    "product": {
        "product_id": "rhoai",
        "display_name": "Red Hat OpenShift AI",
        "docs_repo": "opendatahub-io/opendatahub-documentation",
        "docs_branch": "main",
        "framework": "asciidoc-modular",
        "module_prefixes": {
            "concept": "con_",
            "procedure": "proc_",
            "reference": "ref_",
            "assembly": "assembly_",
            "snippet": "snip_"
        }
    },
    "context_files": [
        {
            "source_type": "documentation",
            "repo": "opendatahub-io/opendatahub-documentation",
            "file_path": "modules/serving/pages/con_model-serving.adoc",
            "content": "...",
            "relevance_score": 0.85,
            "size_bytes": 4521,
            "estimated_tokens": 1130,
            "signals": [...]
        }
    ],
    "metadata": {
        "gathered_at": "2026-04-14T10:30:00Z",
        "total_candidates": 500,
        "selected_candidates": 42,
        "total_tokens": 85000,
        "version_resolved": "2.18",
        "branch_resolved": "release-2.18"
    }
}
```

## Stop conditions

- **Halt**: Jira ticket not found or resolve-jira.sh fails (missing credentials)
- **Halt**: No context sources configured in product config
- **Warn and continue**: Individual repo clone fails (skip that repo)
- **Warn and continue**: Individual file unreadable (skip that file)

## Output

Primary: `workspace/context-package.json`
Report to caller: number of files gathered, total tokens, repos cloned.
