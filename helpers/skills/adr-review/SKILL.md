---
name: adr-review
description: Review an Architectural Decision Record (ADR) using a team of six specialist reviewer subagents and produce a consolidated report as both PDF and PPTX slide deck. Use this skill whenever the user asks to review, critique, audit, or get feedback on an ADR, architecture decision, design doc, or RFC — whether the input is a Markdown file, a .docx document, or pasted text. Trigger even if the user does not explicitly say "ADR"; phrases like "review this architecture decision", "critique this design doc", or "run the reviewer panel on this" should also invoke this skill.
---

# ADR Review Panel

This skill runs a panel of specialist reviewer subagents over an Architectural Decision Record (ADR) and produces a consolidated report in two formats: a PDF document and a PPTX slide deck.

## Why a panel of agents?

Architecture reviews benefit from multiple independent perspectives. A single reviewer tends to anchor on whichever concern they noticed first and under-weight the others. By running specialists in parallel, each focused on one dimension, we get broader, less-biased coverage — and the synthesis step surfaces tensions between perspectives (e.g. "the cheapest option is also the least reversible") that a single reviewer might flatten.

## Workflow

### Step 1 — Prompt for the ADR location and clarifying context

Always ask the user where the ADR is, even if there's a plausible file in context. Accepted inputs:

- A path to a Markdown file (`.md`, `.markdown`)
- A path to a Word document (`.docx`)
- A path to a directory containing multiple ADRs (review each one)

If the user provides a `.docx`, extract the text first using the `document-skills:docx` skill or `python-docx`. If they provide Markdown, read it directly.

**Use the AskUserQuestion tool** to gather any clarifying context the reviewers will need. Ask in a single AskUserQuestion call with multiple questions rather than one-at-a-time. Tailor the questions to what is actually unclear after a quick skim of the ADR — don't ask boilerplate. Typical useful questions:

- **Audience & stakes** — "Who is this review for (author self-check, formal arch board, post-incident retro)?" This shapes tone and severity thresholds.
- **Scope** — "Are there dimensions you want the panel to emphasize or skip?" (e.g., "skip cost, we already costed it elsewhere")
- **Context not in the doc** — "Is there background the ADR assumes readers already know? Team size, existing stack, regulatory environment?"
- **Decision status** — "Is this a draft open to changes, or has the decision already been made and you want a risk audit?"
- **Known concerns** — "Anything you're already worried about that you want the panel to focus on?"

Pass the answers into each reviewer subagent's prompt as a "Review context from the user" block so every reviewer sees the same framing.

### Step 2 — Read and normalize the ADR

Read the file and extract the key sections (context, decision, alternatives considered, consequences). ADRs vary in format (MADR, Nygard, custom) — don't require a specific structure, just pull out what's there. If a section is missing, note it; that absence is itself a finding the reviewers should know about.

### Step 3 — Dispatch the reviewer panel

Spawn **six reviewer subagents in parallel** using the Agent tool. Each gets the full ADR text plus its role-specific prompt from `references/reviewer_prompts.md`. Launch all six in a single message — do not serialize them.

The six reviewers are:

1. **Context & Problem Framing** — Is the problem and its forces clearly articulated? Are the stakeholders and constraints named? Were alternatives genuinely considered or is this a post-hoc rationalization?
2. **Technical Soundness** — Is the proposed solution technically correct and feasible? Does it match the problem? Are there known failure modes or anti-patterns?
3. **Operational & Reliability** — How will this be observed, deployed, and recovered? What are the failure modes in production? Is there a rollback plan? SLOs?
4. **Security & Compliance** — Threat model, data handling, authN/authZ, secrets, regulatory implications. What new attack surface does this introduce?
5. **Cost & Performance** — Resource footprint, cost trajectory at scale, latency/throughput characteristics, capacity planning.
6. **Consequences & Reversibility** — Are the trade-offs honestly stated? How hard is this to undo? Vendor/technology lock-in? Migration path if we change our minds?

Each reviewer must return a structured finding in this shape:

```markdown
## [Reviewer Name]
**Overall assessment:** [Strong / Acceptable / Concerns / Blocking]
**Strengths:** [bullets]
**Concerns:** [bullets, each with the structure below]
**Open questions:** [bullets]
**Recommendations:** [bullets]
```

Each concern must include enough detail for an architect unfamiliar with the review to understand the issue and act on it. Use this structure per concern:

```markdown
- **[severity: low / med / high] [Short title]**
  _What:_ One or two sentences describing the specific gap or problem found in the ADR.
  _So what:_ Why this matters — the concrete consequence if the ADR is accepted without addressing it (e.g., implementer confusion, production risk, blocked downstream ADR).
  _Suggested fix:_ What the author should add, change, or clarify in the document to resolve it. Be specific enough that the author can act without re-reading the full review.
```

This level of detail applies to both the **PDF report** and **Step 3.5** (human-in-the-loop review). The user needs the full _What / So what / Suggested fix_ context to make informed agree/disagree decisions. Only the **PPTX** should use short-form bullets (title + severity) to stay scannable for meetings.

### Step 3.5 — Human-in-the-loop review of findings

Before synthesizing or generating any report, walk the user through the reviewers' findings and let them correct the record. This step exists because the reviewers are operating with limited context — the user often knows things (prior decisions, team dynamics, constraints that didn't make it into the doc) that would change whether a finding is valid.

Present the findings grouped by reviewer. For each reviewer, show:

- The overall assessment
- Each concern and recommendation as a discrete item

Then use the **AskUserQuestion tool** to collect the user's agree/disagree judgment. Batch the questions — don't spam one call per concern. A reasonable approach:

- One AskUserQuestion call per reviewer (6 total), with one question per non-trivial concern, offering options like "Agree", "Disagree — not a real issue", "Partially agree — needs rewording", "Already addressed elsewhere". Include a free-text option so the user can explain.
- Skip questions for concerns that are clearly low-severity and uncontroversial — respect the user's time.

Apply the user's corrections to the findings before synthesis:

- **Disagreed** concerns: remove them, and note in a "Reviewer corrections" sidebar that the user overrode the finding (with their reason if given). Keeping the audit trail matters — a disagreement is data, not an eraser.
- **Partially agreed** concerns: rewrite per the user's guidance.
- **Already addressed** concerns: move them to an "Addressed elsewhere" section rather than deleting, so reviewers of the report understand why they're absent.

The corrected findings — not the raw ones — are what feed into synthesis.

### Step 4 — Synthesize

Once all six reviewers return, synthesize their findings into an overall report. The synthesis is not just concatenation — look for:

- **Agreements** — where multiple reviewers raised the same concern (stronger signal)
- **Tensions** — where reviewers disagree or where one dimension's "win" is another's "loss"
- **Gaps** — dimensions where nobody found much to say (may indicate the ADR didn't address it at all)
- **Top risks** — the 3-5 highest-severity items across the panel
- **Overall recommendation** — Approve / Approve with changes / Needs revision / Reject, with a one-paragraph rationale

### Step 5 — Generate PDF and PPTX reports

Create a `adr-review/` subdirectory next to the input ADR file. Write outputs there:

- `adr-review/<adr-name>-review.pdf`
- `adr-review/<adr-name>-review.pptx`

**PDF structure** — use the `document-skills:pdf` skill (or `reportlab` directly if the skill isn't available):

1. Title page — ADR name, date of review, overall recommendation
2. Executive summary — 3-5 bullets, top risks, overall recommendation
3. One section per reviewer with their full finding. Each concern must include the verbose _What / So what / Suggested fix_ detail so a reader can understand consequences and act on the finding without external context.
4. Synthesis section — agreements, tensions, gaps
5. Appendix — the original ADR text

The PDF is the detailed, self-contained artifact. Err on the side of too much context per concern rather than too little — the reader may not have been in the review conversation.

**PPTX structure** — use the `document-skills:pptx` skill:

1. Title slide
2. Executive summary (overall assessment + top 3 risks)
3. One slide per reviewer (assessment + top 2 concerns + top recommendation)
4. Synthesis slide (agreements / tensions / gaps)
5. Next steps / recommendation slide

Keep slides scannable — bullets, not paragraphs. The PDF is the detailed artifact; the deck is for a 10-minute review meeting.

### Step 6 — Report back

Tell the user where the outputs landed and give a brief summary (overall recommendation + top risks) inline so they don't have to open the files to get the gist.

## Handling edge cases

- **Directory of ADRs** — run the full workflow on each ADR and produce per-ADR outputs. Offer a roll-up report at the end if there are more than three.
- **Very short ADRs** — still run the full panel. A too-thin ADR is itself a finding (the Context & Framing reviewer will flag it).
- **Missing sections** — don't refuse to review. Note the gap and continue.
- **Non-ADR input** (e.g., a general design doc) — proceed anyway; the panel works on any architecture writeup. Note the format in the report.

## Reference files

- `references/reviewer_prompts.md` — The full role prompt for each of the six reviewer subagents. Read this when dispatching the panel.
- `references/report_templates.md` — PDF and PPTX structure templates with example content.
