# PR Comment Review Plugin

This Claude Code plugin helps you analyze Pull Request comments and generate comprehensive action plans with severity rankings, validity assessments, and suggested responses.

## Features

- **Automatic Comment Fetching**: Retrieves all review and general comments from GitHub PRs using `gh` CLI
- **Code Context Inclusion**: Shows actual code snippets (minimum 3 lines) for each inline comment
- **Comment ID Tracking**: Includes unique comment IDs for easy programmatic responses
- **Severity Classification**: Categorizes issues as High, Medium, or Low priority
- **Reasonableness Assessment**: Evaluates whether each comment is valid and actionable
- **Action Planning**: Provides clear steps to address each issue
- **Alternative Approaches**: Offers multiple solution options for complex issues
- **Response Suggestions**: Generates professional replies for each comment
- **Iteration Tracking**: Creates versioned reports to track progress over time

## Installation

This plugin is included in the AI Helpers marketplace. To use it:

1. Ensure this repository is in your Claude Code plugins directory
2. Install and authenticate `gh` CLI:
   ```bash
   # Install: https://cli.github.com/
   gh auth login
   ```
3. The skill will be available as `/pr-comment-review`

## Usage

### Basic Usage

```bash
/pr-comment-review
```

This will analyze the PR URL from your current worktree context (if available).

### Analyze Specific PR

```bash
/pr-comment-review https://github.com/owner/repo/pull/123
```

### Multiple Iterations

Run the skill multiple times as you address issues and receive new comments. Each run creates a new report with an incremented version number:

- First run: `temp/pr_code_review001.md`
- Second run: `temp/pr_code_review002.md`
- And so on...

## Authentication

Authentication is handled through the `gh` CLI:

```bash
gh auth login
```

This will authenticate you with GitHub and grant access to your repositories. The `gh` CLI handles all authentication automatically, including for private repositories.

## Report Structure

The report structure, severity classifications, and formatting guidelines are all defined in the `template.md` file. This ensures consistency across all reports and allows you to customize the format without modifying the skill code.

To customize the report format, simply edit `template.md`. The template includes:
- Complete documentation on severity classifications
- Reasonableness check framework
- Alternative approaches evaluation criteria
- Response tone guidelines
- Issue and response formatting templates

## Example Workflow

1. **Receive PR review comments** from your team
2. **Run the skill**: `/pr-comment-review`
3. **Review the report**: Check `temp/pr_code_review001.md`
4. **Address high-priority issues** using the action plans
5. **Use suggested responses** to reply to reviewers
6. **Re-run after updates**: `/pr-comment-review` creates iteration 002
7. **Track progress** by comparing iteration reports

## Components

### Skill: pr-comment-review

The main skill that orchestrates the analysis process.

**Allowed Tools:** Bash, Read, Write, Glob

### Script: analyze_pr_comments.py

Python script that fetches PR comments using the `gh` CLI.

**Dependencies:**
- `gh` CLI (GitHub CLI) - For fetching PR data
- Standard Python 3 library (no external packages required)

**Supported Platforms:**
- GitHub: `https://github.com/owner/repo/pull/123`

### Template: template.md

Markdown template that defines the structure of the generated PR review reports.

**Location:** `skills/pr-comment-review/template.md`

**Purpose:**
- Provides consistent report formatting
- Defines placeholders for dynamic content
- Includes issue and response templates
- Documents alternative approach evaluation criteria

**Customization:**
The template is fully self-documenting and includes:
- Severity classification criteria
- Reasonableness check framework
- Alternative approaches evaluation guide
- Response tone guidelines
- All formatting instructions

Simply edit `template.md` to customize any aspect of the report generation. All guidelines are embedded in the template as comments, so you don't need to update this README when changing the template structure or criteria.

## Troubleshooting

### No PR URL found
```
Error: No PR URL provided and worktree.pull_request_url is not set.
```

**Solution:** Either provide a PR URL explicitly or ensure your worktree has the PR URL set.

### Authentication failed
```
Error: gh CLI not found or not authenticated.
```

**Solution:**
1. Install `gh` CLI from https://cli.github.com/
2. Run `gh auth login` to authenticate

### Invalid PR URL
```
Error: Unsupported or invalid PR URL format.
```

**Solution:** Ensure the URL matches the supported format:
- GitHub: `https://github.com/owner/repo/pull/123`

## Contributing

To improve this plugin:

1. Follow the [Claude Code Plugin Development Guide](../README.md)
2. Test your changes thoroughly
3. Update documentation
4. Run `make update` to regenerate marketplace data
5. Submit a merge request

## License

This plugin is part of the AI Helpers Marketplace project.
