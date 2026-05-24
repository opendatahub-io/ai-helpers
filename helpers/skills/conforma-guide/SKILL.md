---
name: conforma-guide
description: Educational tool for learning Conforma (Enterprise Contract) concepts, policies, violation types, and troubleshooting workflows. Use when the user asks questions about Conforma, EC policies, what violations mean, or how the conforma skill set works.
metadata:
  author: ODH
---

# Conforma Guide

Educational skill for engineers learning Conforma -- concepts, policies, violation types, and workflows.

## Context Sources (Priority Order)

1. The engineer's question
2. `investigation.doc_search.violation_data` -- if there's an active investigation, use its matched violation YAML as primary context
3. All violation YAML files in the `conforma-doc-search` skill's `references/violations/` directory -- for broader questions ("what violations exist?", "what's the most common?")
4. `conforma-doc-search/references/conforma-policy-reference.md` -- upstream conforma.dev docs for policy explanations
5. `investigation.violation` -- if asking about a specific violation in context, this grounds the explanation

## Instructions

When an engineer asks about Conforma:

1. **Read the relevant reference files** from the `conforma-doc-search` skill's `references/` directory
2. **Answer the question** grounded in the documentation -- do not speculate beyond what the docs say
3. **If the question is about a specific violation code**, use `conforma-doc-search` to look up the per-violation YAML first
4. **Link to upstream docs** where applicable (conforma.dev URLs in the `related` field of violation YAMLs)

## Example Questions This Handles

- "What is Conforma / Enterprise Contract?"
- "What does the missing_sbom violation mean?"
- "How do I create an exception for a policy?"
- "What violations are most common?"
- "How does the troubleshooting workflow work?"
- "What's the difference between a fix and an exception?"

## Scope

This skill is standalone -- it is NOT part of the troubleshooting agent workflow. Engineers invoke it directly via CLI, IDE, or Slack.
