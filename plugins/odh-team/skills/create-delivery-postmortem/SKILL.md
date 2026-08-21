---
name: create-delivery-postmortem
description: >-
  Use when a release delay, missed deadline, or delivery incident needs a structured post-mortem.
  Facilitates context gathering, timeline synthesis, and interactive Five Whys root cause analysis.
  Produces an executive-ready document in HTML or Markdown.
allowed-tools: Read Write Bash(git config:*) Bash(open:*) Bash(xdg-open:*) AskUserQuestion
user-invocable: true
argument-hint: title=<title> release=<release> priority=<priority> format=<html|markdown>
metadata:
  author: AIPCC
  version: "1.0"
  tags:
    - postmortem
    - release
    - root-cause-analysis
    - five-whys
---

# Post-Mortem Create Skill

Facilitate writing a structured post-mortem document for release delays and delivery incidents. The
skill gathers context from the user, synthesizes narrative sections, facilitates an interactive Five
Whys root cause analysis, and produces an executive-ready document.

## Arguments

- **title** (required): Short incident name (e.g., "ROCm RPM Delay")
- **release** (optional): Target release milestone (e.g., "3.5 EA2", "4.0 GA")
- **priority** (optional): critical / high / medium / low
- **format** (optional, default: html): Output format — `html` or `markdown`

Example: `/create-delivery-postmortem title="ROCm RPM Delay" release="3.5 EA2" priority="high"`

## Steps

When invoked:

### Phase 1: Context Gathering

1. **Prompt for context.** Tell the user what input is most valuable, in this order of usefulness:

   1. **Slack threads or conversations** — paste directly. These are the richest source for building
      timelines and identifying who knew what and when.
   2. **JIRA ticket IDs** — look these up for context (committed dates, status changes, comments).
   3. **Committed delivery dates** — when was something promised, and by whom?
   4. **Key people involved** — who owned the deliverable, who raised the risk, who responded.
   5. **Meeting notes or email excerpts** — especially anything documenting commitments or escalations.
   6. **Free-form narrative** — the user's own understanding of what happened.

   Say: "Paste whatever you have — Slack threads, JIRA ticket IDs, notes, narrative. The most useful
   things are conversations that show when risks were raised and committed delivery dates. Send as
   many messages as you need. Say 'done' when you've shared everything."

   Accept input across multiple messages until the user signals completion.

2. **Synthesize narrative sections.** From the gathered context, draft:

   - **Postmortem Summary**: Incident name, author (from `git config user.name`, confirm with user),
     priority, target release.
   - **Executive Summary**: One paragraph — what happened, what the impact was, what was learned.
     Written for a Director-level audience who needs the picture in 30 seconds.
   - **Leadup**: Sequence of events leading to the incident. Use specific dates and actors.
   - **Impact**: Potential or observed delivery impact. Be specific about what was delayed, by how
     long, and what downstream was affected.
   - **Detection and Timeline**: When the team detected or raised the risk. Name people,
     communication channels (Slack, email, meeting), and timestamps.
   - **Response**: Who responded and what was done at each stage. Include delays or obstacles to
     responding. Be specific about handoffs.
   - **Recovery**: When the incident was resolved. Describe how time-to-mitigation could have been
     improved.

3. **Present for review.** Show the drafted sections to the user. Ask them to correct facts, fill
   gaps, and adjust framing. Iterate until the user approves all narrative sections before moving to
   Phase 2.

### Phase 2: Root Cause Analysis — Interactive Five Whys

4. **Draft the Five Whys chain.** Analyze the approved narrative and propose an initial Five Whys
   chain. Start from the surface-level problem statement and work down. For each "why":
   - State the question ("Why did X happen?")
   - Propose the answer
   - Cite evidence from the context (Slack message, date, committed delivery)

5. **Facilitate interactive refinement.** Present the chain and walk through it with the user. At
   each level, actively push back when:

   - A "why" **restates the symptom** rather than identifying a cause. ("The RPMs were late" →
     "The RPMs were delayed" is restating. "The RPMs were late" → "The upstream rebuild took longer
     than the compressed timeline allowed" is a cause.)
   - The chain **stops at human error** ("someone forgot") instead of a systemic gap ("there was no
     process to ensure..."). Always ask: "Why was it possible for this to be forgotten? What system
     or process should have caught this?"
   - A **causal link lacks evidence**. If the user asserts a cause, ask for specifics: "Was the code
     freeze communicated somewhere the team should have seen it? Can you point to where?"
   - The chain **branches** and one branch is being ignored. If there are multiple contributing
     causes, note all branches and explore each.

   Prompt for additional context where the chain is thin. Ask specific questions, not generic ones.

6. **Converge on root cause.** The Five Whys must land on something **systemic and actionable** — a
   process gap, communication breakdown, or missing feedback loop. If the proposed root cause is not
   actionable (e.g., "vendors are slow"), push deeper: "What could we have done earlier to detect or
   mitigate the vendor delay?"

   **Five Whys principles to enforce:**
   - Start from a clear, specific problem statement — not a vague complaint.
   - Each "why" must be a direct cause — not a restatement, correlation, or blame assignment.
   - Don't stop at human error — dig into why the system allowed or failed to prevent the error.
   - Follow all significant branches — if there are multiple contributing causes, explore each.
   - Stop when you reach something systemic and actionable — a process, communication, or structural
     gap that can be fixed.
   - Cite evidence — each causal link should reference specific events, dates, or communications.
   - Five is a guideline, not a rule — stop when you hit root cause, whether at 3 or 7.

7. **Related incidents (optional, but prompt for it).** Ask the user:
   "Has anything like this happened before? If so, what was done about it, and why did it happen
   again despite that mitigation?"

8. **Backlog check (optional, but prompt for it).** Ask the user:
   "Is there anything sitting in your backlog — a tool, a process improvement, an automation — that
   could have prevented this or reduced the impact?"

9. **Lessons learned.** Draft structured lessons based on the Five Whys outcome:
   - **What we learned**: Key insights from the analysis.
   - **What went well**: Anything the team did right during the incident — fast escalation, good
     communication, effective workarounds. Don't skip this section.
   - **What to improve**: Concrete, actionable recommendations. Each recommendation should be
     specific enough to become a JIRA ticket or process change. Avoid vague suggestions like
     "communicate better."

   Present to the user for review. Iterate until approved.

### Phase 3: Output Generation

10. **Read the HTML template.** Read `template.html` from the skill directory (same directory as this
    SKILL.md file).

11. **Generate the document.** Replace each `{{PLACEHOLDER}}` in the template with the approved
    content. Follow these rules:

    - All content sections must use proper HTML tags (`<p>`, `<ul>`, `<li>`, `<ol>`, etc.).
    - **{{TITLE}}**: The incident title from the `title` argument.
    - **{{AUTHOR}}**: The author name confirmed with the user.
    - **{{DATE}}**: Today's date in YYYY-MM-DD format.
    - **{{RELEASE_META}}**: If `release` was provided:
      `<span><span class="label">Release:</span> {release}</span>`. Otherwise, empty string.
    - **{{PRIORITY_META}}**: If `priority` was provided:
      `<span><span class="label">Priority:</span> <span class="priority-badge priority-{priority}">{priority}</span></span>`.
      Otherwise, empty string.
    - **{{EXECUTIVE_SUMMARY}}**: The executive summary paragraph wrapped in `<p>` tags.
    - **{{LEADUP}}**, **{{IMPACT}}**, **{{DETECTION_TIMELINE}}**, **{{RESPONSE}}**, **{{RECOVERY}}**:
      Each section's content using appropriate HTML. Use `<p>` for paragraphs, `<ul>`/`<li>` for
      lists, `<ol>`/`<li>` for ordered sequences.
    - **{{FIVE_WHYS}}**: Render each why as a `<div class="why-step">` containing:
      - `<div class="why-number">` with "W1", "W2", etc.
      - `<div class="why-content">` containing:
        - `<div class="why-question">` with the "Why?" question
        - `<div class="why-answer">` with the answer
        - `<div class="why-evidence">` with the supporting evidence (if any)
      The last why-step is styled differently (red border) automatically by the CSS to highlight the
      root cause level.
    - **{{ROOT_CAUSE}}**: The final root cause statement wrapped in `<p>` tags.
    - **{{RELATED_INCIDENTS}}**: If provided, render as:
      `<h2>Related Incidents</h2>` followed by content. Otherwise, empty string.
    - **{{BACKLOG_CHECK}}**: If provided, render as:
      `<h2>Backlog Check</h2>` followed by content. Otherwise, empty string.
    - **{{LESSONS_LEARNED}}**: Render with three `<h3>` subsections: "What We Learned", "What Went
      Well", "What to Improve", each followed by their content.
    - **{{GENERATED_DATE}}**: Current date and time in YYYY-MM-DD HH:MM format.

    If `format=markdown` was specified, skip the HTML template entirely and generate a standard
    Markdown document with the same section structure using headings, paragraphs, and lists.

12. **Write the output file.** Write to the current working directory:
    - HTML: `postmortem-{slugified-title}.html`
    - Markdown: `postmortem-{slugified-title}.md`

    Slugify the title: lowercase, replace spaces with hyphens, remove non-alphanumeric characters
    except hyphens, collapse multiple hyphens.

13. **Open for review.** Ask the user: "Post-mortem written to `{filename}`. Want me to open it in
    your browser for review?"

    If yes, detect the platform and open:
    ```bash
    if [[ "$(uname)" == "Darwin" ]]; then
      open "{filename}"
    else
      xdg-open "{filename}"
    fi
    ```

14. **Final changes.** Ask: "Want me to make any changes before you share this?"
    Iterate on feedback until the user is satisfied.

## Output

After generating the post-mortem:

- Report the output file path
- Offer to open in browser
- Offer to make final changes
- Do NOT commit to git, create branches, or assume any repo workflow
