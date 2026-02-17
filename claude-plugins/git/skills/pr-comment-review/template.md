<!--
PR COMMENT REVIEW REPORT TEMPLATE

This template defines the structure for PR comment analysis reports.
The skill will read this template and replace placeholders with actual content.

PLACEHOLDERS:
- {ITERATION}: Iteration number (e.g., "001", "002", "003")
- {PR_URL}: Full URL of the pull request
- {ANALYSIS_DATE}: Date and time of analysis (YYYY-MM-DD HH:MM)
- {TOTAL_COMMENTS}: Total number of comments fetched from PR
- {HIGH_SEVERITY_ISSUES}: All high priority issues (formatted per Issue Template below)
- {MEDIUM_SEVERITY_ISSUES}: All medium priority issues (formatted per Issue Template below)
- {LOW_SEVERITY_ISSUES}: All low priority issues (formatted per Issue Template below)
- {COMMENT_RESPONSES}: All suggested responses (formatted per Response Template below)
- {TOTAL_ISSUES}: Total count of all issues identified
- {HIGH_COUNT}: Count of high severity issues
- {MEDIUM_COUNT}: Count of medium severity issues
- {LOW_COUNT}: Count of low severity issues
- {HIGH_EFFORT_ESTIMATE}: Complexity estimate for high severity issues
- {MEDIUM_EFFORT_ESTIMATE}: Complexity estimate for medium severity issues
- {LOW_EFFORT_ESTIMATE}: Complexity estimate for low severity issues

SEVERITY CLASSIFICATION GUIDE:

HIGH SEVERITY - Critical issues requiring immediate attention:
  - Architectural flaws or fundamental design issues
  - Security vulnerabilities (XSS, SQL injection, auth bypass, etc.)
  - Breaking bugs or critical defects
  - Significant performance regressions
  - Data loss or corruption risks
  - Breaking changes to public APIs

MEDIUM SEVERITY - Important improvements that enhance code quality:
  - Code quality and maintainability improvements
  - Missing or inadequate test coverage
  - Logic edge cases not properly handled
  - API design issues (non-breaking)
  - Moderate performance concerns
  - Error handling gaps

LOW SEVERITY - Minor improvements and polish:
  - Code style preferences or formatting issues
  - Typos or minor documentation updates
  - Variable/function naming suggestions
  - Nice-to-have improvements
  - Non-critical refactoring opportunities

REASONABLENESS CHECK FRAMEWORK:

When assessing each comment's validity, consider:
  ✓ Is the feedback technically accurate?
  ✓ Does it align with project standards/conventions?
  ✓ Is the issue actually present in the code?
  ✓ Does the suggestion improve the code meaningfully?
  ✓ Is the scope reasonable for this PR?
  ✓ Are there valid alternative perspectives?

ALTERNATIVE APPROACHES FRAMEWORK:

For complex issues, provide 2 solution options with clear trade-offs:

Option A (Fast/Tactical):
  - Characteristics: Quick implementation, minimal changes, tactical fix
  - Pros: Faster to implement, lower immediate testing burden, less risk
  - Cons: May accumulate technical debt, might need revisiting later
  - Use when: Time-sensitive releases, urgent fixes, low-risk changes

Option B (Robust/Strategic):
  - Characteristics: Comprehensive solution, architectural improvement
  - Pros: Better long-term maintainability, reduces technical debt, scalable
  - Cons: More upfront effort, extensive testing required, higher complexity
  - Use when: Long-term stability matters, refactoring opportunity, high-impact area

Evaluation Criteria:
  1. Implementation speed vs. long-term scalability
  2. Technical debt implications
  3. Impact on other parts of the codebase
  4. Testing requirements and coverage
  5. Team capacity and timeline constraints
  6. Risk tolerance for this component

RESPONSE TONE GUIDELINES:

When crafting suggested responses to reviewers:
  ✓ Professional and collaborative tone
  ✓ Acknowledge the feedback genuinely
  ✓ Be specific about actions you'll take
  ✓ Reference issue IDs for tracking (e.g., "Will address in ISSUE-001")
  ✓ Ask clarifying questions when needed
  ✓ Politely disagree when necessary with clear reasoning
  ✓ Thank reviewers for their time and insights

Examples of good responses:
  - "Great catch! Will fix in ISSUE-001."
  - "Thanks for this suggestion. I'll refactor this as outlined in ISSUE-002."
  - "Good point about edge cases. Added handling in ISSUE-003."
  - "I considered this approach but went with X because Y. Happy to discuss further."

INSTRUCTIONS FOR SKILL:

1. Read this template file
2. For each comment with a file path and line number, read the actual code file to get context
3. Replace all {PLACEHOLDER} values with actual content
4. Format issues using the Issue Template format below (including code context)
5. Format responses using the Response Template format below
6. Remove all template sections (Issue Template, Response Template, and these instructions)
7. Write the final report to temp/pr_code_review{ITERATION}.md

IMPORTANT: For inline code comments (those with file paths and line numbers), you MUST:
- Use the Read tool to fetch the actual code from the file
- Extract at least 3 lines of code context around the commented line
- Include this code context in the "Code Context" section of each issue
- This allows reviewers to see exactly what code is being discussed without switching contexts

-->

# PR Review Action Plan: Iteration {ITERATION}

**PR URL:** {PR_URL}
**Analysis Date:** {ANALYSIS_DATE}
**Total Comments:** {TOTAL_COMMENTS}

---

## Part A: Comment Analysis

### High Severity Issues

{HIGH_SEVERITY_ISSUES}

---

### Medium Severity Issues

{MEDIUM_SEVERITY_ISSUES}

---

### Low Severity Issues

{LOW_SEVERITY_ISSUES}

---

## Part B: Comment Response Mapping

{COMMENT_RESPONSES}

---

## Summary

- **Total Issues:** {TOTAL_ISSUES}
- **High Priority:** {HIGH_COUNT}
- **Medium Priority:** {MEDIUM_COUNT}
- **Low Priority:** {LOW_COUNT}

### Recommended Next Steps

1. Address all High severity issues first
2. Review Medium severity issues and prioritize based on effort/impact
3. Address Low severity issues if time permits

### Estimated Effort

- **High:** {HIGH_EFFORT_ESTIMATE}
- **Medium:** {MEDIUM_EFFORT_ESTIMATE}
- **Low:** {LOW_EFFORT_ESTIMATE}

---

<!--
===================================================================================
TEMPLATE SECTIONS BELOW - Remove these sections from the final report
===================================================================================
-->

## Issue Template

Use this format for EACH issue in the severity sections above:

```markdown
#### ISSUE-{ID}

**Summary:** {BRIEF_DESCRIPTION_OF_THE_ISSUE}
**File:** {FILE_PATH}:{LINE_NUMBER}
**Reviewer:** @{REVIEWER_USERNAME}
**Comment URL:** [Link]({COMMENT_URL})

**Code Context:**
```{LANGUAGE}
{AT_LEAST_3_LINES_OF_CODE_CONTEXT}
```

Include the actual code being discussed (minimum 3 lines):
- Show the line mentioned in the comment
- Include 1-2 lines before for context
- Include 1-2 lines after for context
- Use proper syntax highlighting with the language identifier

**Reasonableness Check:**

{ASSESSMENT_OF_VALIDITY_AND_ACTIONABILITY}

Use the Reasonableness Check Framework above to evaluate:
- Technical accuracy of the feedback
- Alignment with project standards
- Actual presence of the issue
- Meaningful improvement to code quality
- Reasonable scope for this PR

**Proposed Action:**

{CLEAR_SPECIFIC_STEPS_TO_RESOLVE}

Be specific and actionable:
- What files need to be changed
- What code needs to be added/removed/modified
- What tests need to be added/updated
- Any dependencies or prerequisites

**Alternative Approaches:**

<!-- Only include this section for complex issues that have multiple valid solutions -->

- **Option A (Fast/Tactical):** {QUICK_SOLUTION_WITH_TRADEOFFS}
  - Trade-offs: {PROS_AND_CONS}

- **Option B (Robust/Strategic):** {COMPREHENSIVE_SOLUTION_WITH_TRADEOFFS}
  - Trade-offs: {PROS_AND_CONS}

Use the Alternative Approaches Framework above to guide your analysis.

---
```

## Response Template

Use this format for EACH response in Part B:

```markdown
### ISSUE-{ID}

**Original Comment:**
> {FIRST_LINE_OR_KEY_EXCERPT_FROM_COMMENT}
> {CONTINUE_WITH_MORE_LINES_IF_NEEDED_FOR_CONTEXT}

**Suggested Response:**
```
{PROFESSIONAL_CONCISE_REPLY_TO_POST_ON_PR}

Follow the Response Tone Guidelines above:
- Acknowledge the feedback
- Indicate what action you'll take
- Reference the issue ID
- Be collaborative and professional
```
```

---

<!-- END OF TEMPLATE SECTIONS -->
