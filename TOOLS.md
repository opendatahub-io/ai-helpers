# Available Tools

This document lists all available Claude Code tools, Cursor tools, and Gemini Gems in the ODH ai-helpers repository.

## Claude Code Tools

- [Aipcc](#aipcc-claude-code-tool)
- [Git](#git-claude-code-tool)
- [Gitlab](#gitlab-claude-code-tool)
- [Hello World](#hello-world-claude-code-tool)
- [Jira](#jira-claude-code-tool)
- [Konflux](#konflux-claude-code-tool)
- [Python Packaging](#python-packaging-claude-code-tool)
- [Rpm](#rpm-claude-code-tool)
- [Utils](#utils-claude-code-tool)

## Cursor Tools

- [Aipcc](#aipcc-cursor-tool)
- [Jira](#jira-cursor-tool)
- [Konflux](#konflux-cursor-tool)
- [Rpm](#rpm-cursor-tool)

## Gemini Gems

- [Commit Message Assistant](#commit-message-assistant-gemini-gems)
- [Aipcc Adr Assistant](#aipcc-adr-assistant-gemini-gems)
- [Technical Spike & Investigation](#technical-spike-&-investigation-gemini-gems)
- [Email Copilot](#email-copilot-gemini-gems)

## Claude Code Tools

### Aipcc Claude Code Tool

Tools specifically designed for AIPCC workflows and processes

**Commands:**
- **`/aipcc:commit-suggest` `[N]`** - Generate AIPCC Commits style commit messages or summarize existing commits

See [claude-plugins/aipcc/README.md](claude-plugins/aipcc/README.md) for detailed documentation.

### Git Claude Code Tool

Git workflow automation and utilities

**Skills:**
- **shallow-clone** - Perform a shallow clone of a Git repository to a temporary location.

See [claude-plugins/git/README.md](claude-plugins/git/README.md) for detailed documentation.

### Gitlab Claude Code Tool

Tools and skills for interacting with GitLab resources

**Skills:**
- **pipeline-debugger** - Debug and monitor GitLab CI/CD pipelines for merge requests. Check pipeline status, view job logs, and troubleshoot CI failures. Use this when the user needs to investigate GitLab CI pipeline issues, check job statuses, or view specific job logs.

See [claude-plugins/gitlab/README.md](claude-plugins/gitlab/README.md) for detailed documentation.

### Hello World Claude Code Tool

A hello world plugin

**Commands:**
- **`/hello-world:echo` `[name]`** - Hello world plugin implementation

See [claude-plugins/hello-world/README.md](claude-plugins/hello-world/README.md) for detailed documentation.

### Jira Claude Code Tool

Jira workflow automation and utilities

**Commands:**
- **`/jira:sprint-summary` `<sprint-name> [options]`** - Generate comprehensive sprint summaries by analyzing JIRA sprint data, including issue breakdown, progress metrics, and team performance insights.

**Skills:**
- **upload-chat-log** - Export and upload the current chat conversation as a markdown file attachment to a JIRA ticket for later review and documentation.

See [claude-plugins/jira/README.md](claude-plugins/jira/README.md) for detailed documentation.

### Konflux Claude Code Tool

A plugin to analyze and trigger Konflux builds

**Commands:**
- **`/konflux:application` `<subcommand> [args]`** - Manage Konflux application
- **`/konflux:component` `<subcommand> [args]`** - Manage Konflux component

See [claude-plugins/konflux/README.md](claude-plugins/konflux/README.md) for detailed documentation.

### Python Packaging Claude Code Tool

Tools and skills for Python package management

**Skills:**
- **complexity** - Analyze Python package build complexity by inspecting PyPI metadata. Evaluates compilation requirements, dependencies, distribution types, and provides recommendations for wheel building strategies.
- **env-finder** - Investigate environment variables that can be set when building Python wheels for a given project. Analyzes setup.py, CMake files, and other build configuration files to discover customizable build environment variables.
- **license-checker** - Assess license compatibility for Python package redistribution using SPDX.org license database. Evaluates whether a given license allows building and distributing wheels, with real-time license information lookup.
- **license-finder** - Deterministically find license information for Python packages by checking PyPI metadata first, then falling back to Git repository LICENSE files using shallow cloning.
- **source-finder** - Locate source code repositories for Python packages by analyzing PyPI metadata, project URLs, and code hosting platforms like GitHub, GitLab, and Bitbucket. Provides deterministic results with confidence levels.

**Agents:**
- **python-packaging-investigator** - Investigates Python package repositories to analyze build systems, dependencies, and packaging complexity. Provides comprehensive guidance on how packages can be built from source using integrated analysis skills. (Tools: Bash, Read, Grep, Glob, WebFetch, Skill) (Model: sonnet)

See [claude-plugins/python-packaging/README.md](claude-plugins/python-packaging/README.md) for detailed documentation.

### Rpm Claude Code Tool

Tools for working with RPMs

**Commands:**
- **`/rpm:examine` `[copr-chroot-url] OR [build-log-url] [srpm-url] OR [build.log] [specfile|dist-git] [sources]`** - Analyze RPM build.log failures

See [claude-plugins/rpm/README.md](claude-plugins/rpm/README.md) for detailed documentation.

### Utils Claude Code Tool

A generic utilities plugin serving as a catch-all for various helper commands and agents

**Commands:**
- **`/utils:placeholder`** - Placeholder command for the utils plugin

See [claude-plugins/utils/README.md](claude-plugins/utils/README.md) for detailed documentation.

## Cursor Tools

### Aipcc Cursor Tool

Aipcc workflow automation for Cursor AI integration

**Commands:**
- **`/aipcc-commit-suggest` `[N]`** - Generate AIPCC Commits style commit messages or summarize existing commits

See [cursor/README.md](cursor/README.md) for installation and usage instructions.

### Jira Cursor Tool

Jira workflow automation for Cursor AI integration

**Commands:**
- **`/jira-sprint-summary` `<sprint-name> [options]`** - Generate comprehensive sprint summaries by analyzing JIRA sprint data, including issue breakdown, progress metrics, and team performance insights.

See [cursor/README.md](cursor/README.md) for installation and usage instructions.

### Konflux Cursor Tool

Konflux workflow automation for Cursor AI integration

**Commands:**
- **`/konflux-application` `<subcommand> [args]`** - Manage Konflux application
- **`/konflux-component` `<subcommand> [args]`** - Manage Konflux component

See [cursor/README.md](cursor/README.md) for installation and usage instructions.

### Rpm Cursor Tool

Rpm workflow automation for Cursor AI integration

**Commands:**
- **`/rpm-examine` `[copr-chroot-url] OR [build-log-url] [srpm-url] OR [build.log] [specfile|dist-git] [sources]`** - Analyze RPM build.log failures

See [cursor/README.md](cursor/README.md) for installation and usage instructions.

## Gemini Gems

Curated collection of Gemini Gems - specialized AI assistants for various development tasks.

### Commit Message Assistant

I am the AIPCC Commit Message Assistant. Please provide a description of your code changes, and I will generate a well-formatted commit message for you.

**🔗 [Open Commit Message Assistant](https://gemini.google.com/gem/1j7GV5eSdCl3jtT2dYWrRlDpV6q7eBqqc?usp=sharing)**

### Aipcc Adr Assistant

My purpose is to help you generate well-structured Architecture Decision Records (ADRs) in AIPCC. You provide the relevant documents and notes, and I will synthesize that information to populate a predefined ADR template.

**🔗 [Open Aipcc Adr Assistant](https://gemini.google.com/gem/11WO66DX_4-MQHIF6fj4LeM8dKxDzkz17?usp=sharing)**

### Technical Spike & Investigation

My purpose is to help an engineer conduct a technical spike for a new feature, library, initiative, or component. Note: gems don't have access to deep research so if you need the Spike to perform some research on the Internet, you'll not want to use this Gem and use regular chat sessions.

**🔗 [Open Technical Spike & Investigation](https://gemini.google.com/gem/1PAt1u0cEtMbzqjl3Kp3TAzaUft3qrkXw?usp=sharing)**

### Email Copilot

My purpose is to take your minimal, raw notes and expand them into complete, polished email drafts, acting as your thought partner.

**🔗 [Open Email Copilot](https://gemini.google.com/gem/1P0wg_pwCga6YDVKfd3enWY1CRh2EzuXI?usp=sharing)**

See [gemini-gems/README.md](gemini-gems/README.md) for more information about Gemini Gems and how to contribute.
