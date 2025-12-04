---
name: source-finder
description: Locate source code repositories for Python packages by analyzing PyPI metadata, project URLs, and code hosting platforms like GitHub, GitLab, and Bitbucket. Provides deterministic results with confidence levels.
allowed-tools: [Bash, WebSearch, WebFetch]
---

# Source Finder

Locates source code repositories for Python packages with confidence scoring.

## Usage

To find a source repository for a given package:

1. Run the finder script, for example:

```
# Find repository
$ ./scripts/finder.py requests

# Output structure:
{
  "url": "https://github.com/psf/requests",
  "confidence": "high",
  "method": "pypi_metadata_project_urls.Source",
  "package_name": "requests"
}
```

2. Parse the JSON output:

- `url`: Repository URL (or `null` if not found)
- `confidence`: `high`, `medium`, or `low`
- `method`: How the URL was found
- `package_name`: the package that was searched

3. If confidence is `low` or `url` is `null`, use WebSearch: `<package_name> python github repository`

4. Present results with confidence level clearly indicated

## Output Format

As a result, provide structured output including:

- Repository URL
- Confidence level (high/medium/low)
- Method used to find the repository
- Additional context or warnings
