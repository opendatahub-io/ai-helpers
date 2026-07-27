---
name: security-alert
description: >-
  Use this skill to filter a pre-fetched set of Hacker News stories down to
  those that report supply-chain security threats relevant to software
  developers — including malicious packages on npm or PyPI, compromised
  developer tooling, and attacks targeting source code repositories or CI/CD
  infrastructure. Reads stories from stories.json in the workspace, performs
  semantic analysis (fetching HN threads when the title alone is ambiguous), and writes the stories
  worth alerting on to findings.json.
author: AIPCC
allowed-tools: Bash(curl:https://hn.algolia.com/*) Read Write
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

**Include a story only if it describes an adversarial attack on the software
supply chain itself — meaning the dependency, build, or distribution
infrastructure has been compromised or weaponized. Specifically:**

**Malicious or typosquatted packages**
- A package published to npm, PyPI, or another public registry that
  contains malicious code, credential theft, data exfiltration, or
  unexpected execution at install or import time
- A typosquatting campaign or dependency confusion attack targeting a
  public registry

**Compromised maintainer accounts or signing keys**
- A package maintainer account on a registry or code host has been taken
  over and used to push unauthorized code
- Package signing keys have been stolen or misused

**Backdoors in open-source dependencies**
- Malicious code inserted into an open-source library, framework, or
  tool that developers pull as a dependency

**Attacks on source code repositories or CI/CD infrastructure**
- Poisoned build steps, compromised CI runners, leaked secrets in build
  pipelines, or unauthorized pushes to a repository
- A compromised artifact registry, container registry, package mirror,
  or signing infrastructure

**Dependency confusion or namespace hijacking**
- An attacker claiming an internal package name on a public registry to
  trick build systems into pulling the malicious version

**Exclude** stories about:
- IDEs, editors, or tools generating code with insecure patterns — this
  is a code-quality issue, not a supply-chain attack (e.g. an AI code
  assistant suggesting vulnerable code)
- Platform outages or authentication incidents — operational disruptions
  are not adversarial supply-chain compromises (e.g. a code host's auth
  service going down and breaking CI/CD)
- Project governance or policy decisions — changes to contribution rules,
  PR policies, or project management are not security threats (e.g. a
  project restricting PRs or changing maintainership criteria)
- General vulnerability disclosures in end-user software unrelated to
  the dependency supply chain (e.g. a browser RCE, an OS privilege
  escalation)
- General data breaches unrelated to developer tooling or source code
- Security research or proof-of-concept disclosures with no active
  exploitation of a supply-chain vector
- Geopolitical or policy news

**The test:** has the *dependency, build, or distribution pipeline* been
adversarially compromised or weaponized? If the answer is no — if the
story describes a quality issue, an outage, a policy decision, or a
vulnerability that only affects end-users of software — exclude it.

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
