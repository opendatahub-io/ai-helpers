---
name: security-alert
description: >-
  Use this skill to filter a pre-fetched set of Hacker News stories down to
  those that report supply-chain security threats relevant to the Red Hat /
  RHEL ecosystem, Python (PyPI/pip), or JavaScript/TypeScript (npm/yarn/pnpm).
  Reads stories from stories.json in the workspace, performs semantic analysis
  (fetching HN threads when the title alone is ambiguous), and writes the
  stories worth alerting on to findings.json.
author: AIPCC
allowed-tools: Bash(curl:https://hn.algolia.com/*) Read Write
---

# Security Alert: Developer Supply-Chain Threat Filter

Read a set of Hacker News stories and decide which ones are worth alerting on
— meaning they plausibly report a supply-chain threat that affects the **Red
Hat / RHEL ecosystem, Python, or JavaScript/TypeScript**. Write those stories
to `findings.json`.

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

Apply two independent tests to each story. A story must **pass both** to be
included. This is a judgment call — do not rely on keyword matching alone.

---

### Test A — Ecosystem relevance (scope gate)

The story must directly involve one of these ecosystems:

**Python**
- PyPI packages, pip, pipenv, Poetry, conda, or any Python-specific
  tooling or runtime
- Python-language libraries, frameworks, or build tools (e.g. setuptools,
  wheel, twine)

**JavaScript / TypeScript**
- npm, yarn, pnpm, Bun, Deno, or any JS/TS package registry or runtime
- Node.js tooling, bundlers (webpack, Vite, Rollup, esbuild), or
  JS/TS-language libraries and frameworks

**Red Hat / RHEL ecosystem**
- RHEL, Fedora, CentOS Stream, or RPM-based package repositories (dnf,
  rpm, COPR, official Red Hat repos)
- Red Hat products and platforms: OpenShift, OKD, Ansible, Ansible
  Galaxy/Automation Hub, Quay.io, Podman, Buildah, RHACS, Satellite,
  Insights, or any `registry.redhat.io` / `registry.access.redhat.com`
  image
- Red Hat developer tooling: CodeReady, Developer Hub, RHDH, RHEL AI,
  InstructLab, or official Red Hat SDKs

**Exclude** stories where the affected ecosystem is clearly something else
entirely — Go modules, Rust crates, Ruby gems, Java/Maven, .NET NuGet,
Swift, Dart, PHP Composer, etc. — even if the attack technique is novel or
interesting.

**Ecosystem uncertain?** If you cannot confirm the story touches one of
the three ecosystems above (even after reading the HN thread), **exclude
it**. Reducing false positives is the priority here.

---

### Test B — Supply-chain attack (threat gate)

The story must also describe an adversarial attack on the software supply
chain itself — the dependency, build, or distribution infrastructure has
been compromised or weaponized. Specifically:

**Malicious or typosquatted packages**
- A package published to npm, PyPI, or another in-scope registry that
  contains malicious code, credential theft, data exfiltration, or
  unexpected execution at install or import time
- A typosquatting campaign or dependency confusion attack

**Compromised maintainer accounts or signing keys**
- A registry account taken over to push unauthorized code
- Package signing keys stolen or misused

**Backdoors in open-source dependencies**
- Malicious code inserted into a library, framework, or tool that
  developers pull as a dependency

**Attacks on source code repositories or CI/CD infrastructure**
- Poisoned build steps, compromised CI runners, leaked secrets in
  pipelines, or unauthorized pushes to a repository
- A compromised artifact registry, container registry, package mirror,
  or signing infrastructure

**Dependency confusion or namespace hijacking**
- An attacker claiming an internal package name on a public registry

**Exclude** stories about:
- IDEs, editors, or tools generating code with insecure patterns — code
  quality, not a supply-chain attack
- Platform outages or auth incidents — operational, not adversarial
- Project governance or policy decisions
- General vulnerability disclosures that affect only end-users and not
  the dependency supply chain (e.g. a browser RCE, an OS privilege
  escalation in an unrelated OS)
- General data breaches unrelated to developer tooling or source code
- Security research or proof-of-concept disclosures with no active
  exploitation of a supply-chain vector
- Geopolitical or policy news

**The test:** has the *dependency, build, or distribution pipeline* been
adversarially compromised or weaponized *in an in-scope ecosystem*? If
either part of that test fails, exclude the story.

---

Fetch the HN thread for any story that is not immediately obvious noise
(title makes it unambiguously out of scope). Cap total thread fetches at
**15** per run — if you reach the cap, **exclude** remaining ambiguous
stories rather than including them unchecked.

```bash
curl -sf "https://hn.algolia.com/api/v1/items/<id>"
```

If this exits non-zero or returns no data (network error, timeout), decide
based on the title alone and proceed — do not let a single fetch failure
block the run.

While reading the thread:
- Apply both tests and decide whether to include this story.
- **Summarize** the linked article or post in one sentence. Capture what
  happened, what was compromised, and who is affected. Store as `article_summary`.

**When uncertain about ecosystem relevance (Test A), exclude.** When
uncertain about whether a confirmed in-scope story describes a real
supply-chain attack (Test B), include — a missed real threat is worse than
one extra alert.

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
| Uncertain about ecosystem (Test A) | Exclude it |
| Uncertain about threat type (Test B), ecosystem confirmed | Include it |
