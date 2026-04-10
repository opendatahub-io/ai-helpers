# Report Templates

## PDF Template

```
[TITLE PAGE]
  ADR Review: <ADR title>
  Reviewed: <date>
  Overall Recommendation: <Approve | Approve with changes | Needs revision | Reject>

[EXECUTIVE SUMMARY]
  - Overall assessment (1 sentence)
  - Top 3-5 risks (each with severity)
  - Recommended next steps (3 bullets)

[REVIEWER FINDINGS]
  For each of the six reviewers:
    ## <Reviewer Name>
    Overall: <Strong | Acceptable | Concerns | Blocking>
    Strengths: ...
    Concerns:
      For each concern:
        [severity: low / med / high] Short title
        What: specific gap or problem in the ADR (1-2 sentences)
        So what: concrete consequence if unaddressed (implementer confusion, production risk, etc.)
        Suggested fix: what the author should add/change/clarify to resolve it
    Open questions: ...
    Recommendations: ...

[SYNTHESIS]
  Agreements across reviewers:
  Tensions between dimensions:
  Gaps (dimensions the ADR didn't address):
  Top risks (consolidated):
  Overall recommendation with rationale:

[APPENDIX]
  Original ADR text
```

## PPTX Template

Slide 1 — Title
  - ADR name
  - Review date
  - Overall recommendation badge

Slide 2 — Executive Summary
  - Overall assessment (1 line)
  - Top 3 risks
  - Recommendation

Slides 3-8 — One per Reviewer
  - Reviewer name as title
  - Assessment (Strong/Acceptable/Concerns/Blocking)
  - Top 2 concerns
  - Top recommendation

Slide 9 — Synthesis
  - Where reviewers agreed
  - Where they disagreed
  - What nobody covered (gaps)

Slide 10 — Next Steps
  - Overall recommendation
  - 3-5 action items
  - Open questions to resolve before proceeding

## Style notes

- PDF is the detailed artifact; preserve full reviewer text including _What / So what / Suggested fix_ for every concern. A reader should be able to understand consequences and act on findings without external context.
- Slides are for a meeting — bullets, not paragraphs. Max 5 bullets/slide, max ~10 words/bullet.
- Use severity color cues where possible (red = high, amber = med, grey = low).
- Keep the title slide and exec summary self-contained — someone should be able to get the bottom line from those two alone.
