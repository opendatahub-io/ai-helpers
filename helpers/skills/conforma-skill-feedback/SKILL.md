---
name: conforma-skill-feedback
description: Report quality issues with any conforma-* skill (hallucinations, wrong analysis, incorrect fix suggestions) as structured Jira tickets. Use when the user wants to report that a conforma skill produced incorrect or unhelpful output.
allowed-tools: Bash(acli:*)
metadata:
  author: ODH
---

# Conforma Skill Feedback

Lets engineers report quality issues with any conforma-* skill as structured Jira tickets.

## When to Use

- The AI produced a hallucinated root cause
- The suggested fix was wrong or harmful
- The analysis missed the actual problem
- The documentation lookup returned irrelevant content

## Instructions

When the engineer reports a problem with a conforma skill:

1. **Gather details**:
   - Which skill produced the issue (e.g., `conforma-violation-analyze`)
   - What the AI said (the incorrect output)
   - What the correct answer should be
   - Severity (how harmful was the bad output)

2. **Structure the report**:
   - Extract the skill name, incorrect output, expected output, severity
   - If a handover document is available, attach it as evidence

3. **Create a Jira ticket** using the `acli` CLI:
   - Summary: `[conforma-skill-feedback] {skill_name}: {brief description}`
   - Description: structured report with incorrect vs expected output
   - Attach the full handover JSON if available

   ```bash
   acli jira create-issue \
     --project RHOAIENG \
     --type Bug \
     --summary "[conforma-skill-feedback] conforma-violation-analyze: hallucinated root cause" \
     --description "Skill: conforma-violation-analyze
   Incorrect output: Suggested missing SBOM task, but task is present
   Expected output: Should have identified expired signing key
   Severity: high — engineer applied wrong fix
   Evidence: see attached handover.json" \
     --attach handover.json
   ```

## Feedback Loop

These tickets feed back into improving:
- `references/violations/*.yaml` documentation files
- Skill SKILL.md instructions and prompts
- The `conforma-violation-analyze` analysis approach
