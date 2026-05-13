---
name: security-alert
description: >-
  Use this skill to filter a pre-fetched set of Hacker News stories down to
  those that report supply-chain security threats relevant to software
  developers — including malicious packages on npm or PyPI, compromised
  developer tooling, and attacks targeting source code repositories or CI/CD
  infrastructure. Reads stories from stories.json in the workspace, performs
  semantic analysis (fetching HN threads as needed), and writes the stories
  worth alerting on to findings.json.
author: AIPCC
allowed-tools: Bash(curl:https://hn.algolia.com/*) Read Write
model: claude-sonnet-4-5
---

# Security Alert: Developer Supply-Chain Threat Filter

Read a set of Hacker News stories and decide which ones are worth alerting on
— meaning they plausibly report a threat to the software supply chain or
developer infrastructure. Write those stories to `findings.json`.

The pipeline controls when this skill runs and has already built the candidate
story list. The scope here is semantic analysis only — do not re-fetch or
reorder the candidate list, manage state, check registries, or post to Slack. Fetching
individual HN thread detail via the Algolia items API is permitted up to the
cap in Step 2.

Run the steps below in order. At any early-exit point, stop and take no
further action.

---

## Step 1: Read candidate stories

Read `stories.json` from the workspace:

```bash
if [ ! -f stories.json ]; then
  echo '[]' > findings.json
  exit 0
fi
cat stories.json
```

Each story in the array has:

| Field | Description |
|---|---|
| `id` | HN item ID (string) |
| `title` | Story headline |
| `url` | Linked article URL, or HN thread URL if no external link |
| `hn_url` | Direct HN thread link |

If the array is empty, **stop here** and write an empty findings array to
`findings.json`.

---

## Step 2: Filter each story

Read each story title. Decide whether it is reporting a threat relevant to
software developers or the software supply chain. This is a judgment call —
do not rely on keyword matching. A relevant story may use none of the obvious
terms.

**Include a story if it describes any of the following:**

**Package-level threats (npm / PyPI)**
- A specific package containing malicious code, credential theft,
  data exfiltration, or unexpected execution at install or import time
- A supply-chain attack, typosquatting campaign, dependency confusion
  attack, or backdoor inserted into a package

**Developer tooling threats**
- A malicious or compromised IDE extension, editor plugin, build tool,
  linter, formatter, or code generator
- A compromised CLI tool distributed via a package manager or installer

**Source code and repository threats**
- Unauthorized access to, or exfiltration from, a source code host
  (GitHub, GitLab, Bitbucket, etc.)
- A breach affecting developer credentials, tokens, or SSH keys stored
  in or used by a code host

**CI/CD and infrastructure threats**
- A compromised CI/CD system, build pipeline, or artifact registry
- An attack on infrastructure widely used in software development
  (container registries, package mirrors, signing infrastructure)

**Exclude** stories about:
- CVEs or vulnerabilities in software that developers *use* (browsers, OSes,
  editors) where the attack vector is not the software supply chain itself —
  e.g. a Chromium bug exploited via the browser is not a supply-chain attack
- General data breaches unrelated to developer tooling or source code
- Vulnerabilities in deployed/production software with no supply-chain angle
- Geopolitical or policy news
- Security research or proof-of-concept disclosures with no active exploitation
  of a supply-chain vector

**The test:** would a developer's *build, publish, or dependency pipeline* be
compromised? If the answer is no — if the threat only affects them as an
end-user of software — exclude it.

Fetch the HN thread for any story that is not immediately obvious noise (title
makes it unambiguously unrelated). Cap total thread fetches at **15** per run —
if you reach the cap, include remaining untouched stories in findings so they
are not silently dropped.

```bash
curl -sf "https://hn.algolia.com/api/v1/items/<id>"
```

If this exits non-zero or returns no data (network error, timeout), decide
based on the title alone and proceed — do not let a single fetch failure block
the run.

While reading the thread:
- Decide whether to include this story.
- **Summarize** the linked article or post in one sentence. Capture what
  happened, what was compromised, and who is affected. Store as `article_summary`.

**When uncertain, include the story.** A false negative (missing a real threat)
is worse than an extra alert that turns out to be nothing.

---

## Step 3: Write findings.json

Write an array of the stories worth alerting on to `findings.json`. Write an
empty array if no stories were relevant.

Each object:

```json
{
  "hn_id":             "<HN story ID>",
  "package":           "<named package or tool, or empty string if none>",
  "registry":          "npm" | "pypi" | "",
  "versions_affected": "<version range, 'unknown', or empty>",
  "article_summary":   "<one sentence: what happened, what was compromised, who is affected>",
  "hn_title":          "<story headline>",
  "hn_url":            "<https://news.ycombinator.com/item?id=...>"
}
```

For stories **without a specific npm/PyPI package** (e.g. a compromised VSCode
extension, a GitHub breach, a CI/CD attack): leave `package`, `registry`, and
`versions_affected` as empty strings. The `article_summary` is the primary
signal — make it count.

Write the array to `findings.json` in the workspace and validate it:

```bash
cat > findings.json << 'EOF'
[
  { ... }
]
EOF
jq . findings.json >/dev/null
```

---

## Error handling

| Scenario | Behavior |
|---|---|
| `stories.json` missing | Write `[]` to `findings.json`; exit 0 |
| `stories.json` present but empty array | Write `[]` to `findings.json`; stop |
| Thread fetch fails (curl non-zero) | Decide on title alone; proceed |
| No stories are relevant | Write `[]` to `findings.json`; stop |
| Uncertain whether a story is relevant | Include it |
