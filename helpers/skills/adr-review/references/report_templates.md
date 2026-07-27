# Report Templates

## PDF Template

```text
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

## PPTX styling

When generating the PPTX with `python-pptx`, apply these styling rules to produce
a clean, professional deck rather than plain white slides with default fonts.

### Color palette (RGB hex)

| Role | Hex | Usage |
|------|-----|-------|
| Dark background | #1B2A4A | Title slide background, section headers |
| White text | #FFFFFF | Text on dark backgrounds |
| Light grey bg | #F4F5F7 | Content slide backgrounds |
| Dark text | #2D3748 | Body text on light backgrounds |
| Muted text | #718096 | Subtitles, metadata, dates |
| Accent blue | #3182CE | Section title underlines, key labels |
| Severity red | #C53030 | [high] severity tags |
| Severity amber | #C05621 | [med] severity tags |
| Severity grey | #718096 | [low] severity tags |
| Strong/Approve | #276749 | Strong/Approve verdict badges |
| Acceptable | #2B6CB0 | Acceptable verdict badges |
| Concerns | #C05621 | Concerns verdict badges |
| Blocking/Reject | #C53030 | Blocking/Reject verdict badges |

### Typography

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Title slide heading | Calibri | 36pt | Bold | White |
| Title slide subtitle | Calibri | 20pt | Normal | #A0AEC0 |
| Slide title | Calibri | 26pt | Bold | #1B2A4A |
| Slide subtitle | Calibri | 14pt | Normal | #718096 |
| Bullet text | Calibri | 16pt | Normal | #2D3748 |
| Severity tag | Calibri | 16pt | Bold | per severity color |
| Verdict badge | Calibri | 14pt | Bold | per verdict color |

### Slide layout rules

- **Slide size:** 13.333 x 7.5 inches (widescreen 16:9).
- **Title slide:** Dark background (#1B2A4A). Title centered vertically in upper third. Subtitle (ADR name) below. Date and verdict in lower third, muted.
- **Content slides:** Light grey background (#F4F5F7). Slide title in top-left at (0.8in, 0.5in) with width 11.5in. A thin accent line (2pt, #3182CE) below the title at ~1.15in from top. Body content starts at 1.4in from top with 0.8in left margin.
- **Verdict badges on reviewer slides:** Show the verdict (Strong/Acceptable/Concerns/Blocking) as colored text next to or below the reviewer name, using the verdict color.
- **Severity tags:** When listing concerns, prefix with [high], [med], or [low] in the matching severity color. The rest of the bullet text stays in dark text color.
- **Max 5 bullets per slide, max ~12 words per bullet.** If a reviewer has more than 2 high/med concerns, pick the top 2.
- **Synthesis and Next Steps slides** use the same content-slide layout.
- **No clip art, no stock images, no logos.** Clean typography only.

### python-pptx implementation notes

To set a slide background color:

```python
from pptx.oxml.ns import qn
bg = slide.background
fill = bg.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0x1B, 0x2A, 0x4A)
```

To add a thin accent line below the title:

```python
from pptx.util import Inches, Pt, Emu
line = slide.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.15), Inches(11.5), Pt(2)
)
line.fill.solid()
line.fill.fore_color.rgb = RGBColor(0x31, 0x82, 0xCE)
line.line.fill.background()  # no border on the shape
```

To apply a font with color to a run:

```python
run = paragraph.add_run()
run.text = "[high]"
run.font.size = Pt(16)
run.font.bold = True
run.font.color.rgb = RGBColor(0xC5, 0x30, 0x30)
run.font.name = "Calibri"
```

## Style notes

- PDF is the detailed artifact; preserve full reviewer text including _What / So what / Suggested fix_ for every concern. A reader should be able to understand consequences and act on findings without external context.
- Slides are for a meeting — bullets, not paragraphs. Max 5 bullets/slide, max ~12 words/bullet.
- Use severity color cues where possible (red = high, amber = med, grey = low).
- Keep the title slide and exec summary self-contained — someone should be able to get the bottom line from those two alone.
