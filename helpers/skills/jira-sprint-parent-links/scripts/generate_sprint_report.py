#!/usr/bin/env python3
"""
Jira Sprint Parent Links Report Generator

This script generates a comprehensive report of issues in a Jira sprint,
including parent and epic links, hierarchy summary, and parent epic details.

Usage:
    python generate_sprint_report.py <team_number> <sprint_name> [--output FILE]

Examples:
    python generate_sprint_report.py 5800 "Sprint 25"
    python generate_sprint_report.py 5800 "Sprint 25" --output sprint_25_report.md

Features:
    - Hierarchy Summary with Initiative/Feature breakdown
    - Parent Epic Details with issue type classification
    - Epic Distribution with parent epic links
    - Comprehensive issue list with parent/epic relationships
    - All AIPCC issues properly linked to Jira
"""

import argparse
import json
import sys
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Set


def format_issue_table(issues: List[Dict[str, Any]]) -> str:
    """Format issues into a markdown table."""
    table = []
    table.append("| Issue Key | Summary | Type | Status | Assignee | Parent Link | Epic Link |")
    table.append("|-----------|---------|------|--------|----------|-------------|-----------|")

    for issue in issues:
        key = issue['key']
        summary = issue['summary']
        issue_type = issue.get('issue_type', {}).get('name', 'Unknown')
        status = issue.get('status', {}).get('name', 'Unknown')

        assignee = issue.get('assignee', {}).get('display_name', 'Unassigned')

        # Get parent and epic links from custom fields
        custom_fields = issue.get('custom_fields', {})
        parent_link = custom_fields.get('customfield_12313140', {}).get('value')
        epic_link = custom_fields.get('customfield_12311140', {}).get('value')

        parent_display = f"[{parent_link}](https://issues.redhat.com/browse/{parent_link})" if parent_link else "-"
        epic_display = f"[{epic_link}](https://issues.redhat.com/browse/{epic_link})" if epic_link else "-"

        jira_url = f"https://issues.redhat.com/browse/{key}"

        table.append(
            f"| [{key}]({jira_url}) | {summary} | {issue_type} | {status} | "
            f"{assignee} | {parent_display} | {epic_display} |"
        )

    return "\n".join(table)


def get_epic_info(issues: List[Dict[str, Any]], epic_data: Dict[str, Any] = None) -> Dict[str, Dict[str, Any]]:
    """Extract epic information from issues and optional epic data."""
    epic_info = {}
    epic_counts = defaultdict(int)

    for issue in issues:
        custom_fields = issue.get('custom_fields', {})
        epic_link = custom_fields.get('customfield_12311140', {}).get('value')

        if epic_link:
            epic_counts[epic_link] += 1
            if epic_link not in epic_info:
                epic_info[epic_link] = {
                    'count': 0,
                    'description': '',
                    'parent_key': None,
                    'parent_type': None
                }

    # Update counts
    for epic, count in epic_counts.items():
        epic_info[epic]['count'] = count

    # Add epic data if provided (from Jira API calls)
    if epic_data:
        for epic_key, data in epic_data.items():
            if epic_key in epic_info:
                epic_info[epic_key].update(data)

    return epic_info


def generate_hierarchy_summary(epic_info: Dict[str, Dict[str, Any]]) -> str:
    """Generate hierarchy summary with Initiative/Feature breakdown."""
    # Group by parent type
    initiatives = {}
    features = {}

    for epic_key, info in epic_info.items():
        parent_key = info.get('parent_key')
        parent_type = info.get('parent_type')

        if parent_type == 'Initiative':
            if parent_key not in initiatives:
                initiatives[parent_key] = {
                    'epics': [],
                    'total_issues': 0,
                    'description': info.get('parent_description', '')
                }
            initiatives[parent_key]['epics'].append(epic_key)
            initiatives[parent_key]['total_issues'] += info['count']
        elif parent_type == 'Feature':
            if parent_key not in features:
                features[parent_key] = {
                    'epics': [],
                    'total_issues': 0,
                    'description': info.get('parent_description', '')
                }
            features[parent_key]['epics'].append(epic_key)
            features[parent_key]['total_issues'] += info['count']

    lines = []
    lines.append("## Hierarchy Summary")
    lines.append("")

    # Count dominant initiative
    dominant_initiative = None
    max_issues = 0
    for init_key, init_data in initiatives.items():
        if init_data['total_issues'] > max_issues:
            max_issues = init_data['total_issues']
            dominant_initiative = init_key

    if dominant_initiative:
        lines.append(f"Sprint 25 work is organized under **{len(initiatives)} Initiatives** and **{len(features)} Feature{'s' if len(features) != 1 else ''}**. "
                    f"The dominant initiative ([{dominant_initiative}](https://issues.redhat.com/browse/{dominant_initiative})) "
                    f"accounts for {initiatives[dominant_initiative]['total_issues']} issues.")
    lines.append("")

    if initiatives:
        lines.append("### Initiative Breakdown")
        for idx, (init_key, init_data) in enumerate(sorted(initiatives.items(),
                                                           key=lambda x: x[1]['total_issues'],
                                                           reverse=True), 1):
            desc = init_data['description'] or init_key
            lines.append(f"{idx}. **[{init_key}](https://issues.redhat.com/browse/{init_key})** - {desc}: "
                        f"{init_data['total_issues']} issues across {len(init_data['epics'])} child epic{'s' if len(init_data['epics']) > 1 else ''}")
        lines.append("")

    if features:
        lines.append("### Feature Breakdown")
        for idx, (feat_key, feat_data) in enumerate(sorted(features.items(),
                                                           key=lambda x: x[1]['total_issues'],
                                                           reverse=True), 1):
            desc = feat_data['description'] or feat_key
            lines.append(f"{idx}. **[{feat_key}](https://issues.redhat.com/browse/{feat_key})** - {desc}: "
                        f"{feat_data['total_issues']} issues under {len(feat_data['epics'])} child epic{'s' if len(feat_data['epics']) > 1 else ''}")
        lines.append("")

    return "\n".join(lines)


def generate_parent_epic_details(epic_info: Dict[str, Dict[str, Any]]) -> str:
    """Generate parent epic details section."""
    parent_epics = {}

    for epic_key, info in epic_info.items():
        parent_key = info.get('parent_key')
        parent_type = info.get('parent_type')
        parent_desc = info.get('parent_description')

        if parent_key:
            if parent_key not in parent_epics:
                parent_epics[parent_key] = {
                    'type': parent_type or 'Unknown',
                    'description': parent_desc or parent_key,
                    'child_epics': [],
                    'total_issues': 0
                }
            parent_epics[parent_key]['child_epics'].append(epic_key)
            parent_epics[parent_key]['total_issues'] += info['count']

    lines = []
    lines.append("## Parent Epic Details")
    lines.append("")

    # Sort by total issues descending
    for parent_key, parent_data in sorted(parent_epics.items(),
                                         key=lambda x: x[1]['total_issues'],
                                         reverse=True):
        child_count = len(parent_data['child_epics'])
        lines.append(f"- **[{parent_key}](https://issues.redhat.com/browse/{parent_key})** "
                    f"*({parent_data['type']})*: {parent_data['description']} "
                    f"*({child_count} child epic{'s' if child_count > 1 else ''}, "
                    f"{parent_data['total_issues']} total issues)*")
    lines.append("")

    return "\n".join(lines)


def generate_epic_summary(issues: List[Dict[str, Any]], epic_info: Dict[str, Dict[str, Any]] = None) -> str:
    """Generate epic distribution summary with parent links."""
    epic_counts = defaultdict(int)

    for issue in issues:
        custom_fields = issue.get('custom_fields', {})
        epic_link = custom_fields.get('customfield_12311140', {}).get('value')

        if epic_link:
            epic_counts[epic_link] += 1
        else:
            epic_counts['No Epic'] += 1

    table = []
    table.append("| Epic Key | Description | Issue Count | Epic Parent Link |")
    table.append("|----------|-------------|-------------|------------------|")

    # Sort by count descending
    for epic, count in sorted(epic_counts.items(), key=lambda x: x[1], reverse=True):
        if epic == 'No Epic':
            table.append(f"| No Epic | Standalone issues | {count} | - |")
        else:
            epic_url = f"https://issues.redhat.com/browse/{epic}"
            description = epic_info.get(epic, {}).get('description', '-') if epic_info else '-'
            parent_key = epic_info.get(epic, {}).get('parent_key') if epic_info else None
            parent_display = f"[{parent_key}](https://issues.redhat.com/browse/{parent_key})" if parent_key else "-"
            table.append(f"| [{epic}]({epic_url}) | {description} | {count} | {parent_display} |")

    return "\n".join(table)


def generate_parent_summary(issues: List[Dict[str, Any]]) -> str:
    """Generate parent link summary."""
    parent_count = 0
    epic_count = 0
    no_link_count = 0

    parent_links = []

    for issue in issues:
        custom_fields = issue.get('custom_fields', {})
        parent_link = custom_fields.get('customfield_12313140', {}).get('value')
        epic_link = custom_fields.get('customfield_12311140', {}).get('value')

        if parent_link:
            parent_count += 1
            parent_links.append((issue['key'], parent_link))

        if epic_link:
            epic_count += 1

        if not parent_link and not epic_link:
            no_link_count += 1

    summary = []
    summary.append(f"- **Issues with Parent Links:** {parent_count}")
    if parent_links:
        for issue_key, parent_key in parent_links:
            parent_url = f"https://issues.redhat.com/browse/{parent_key}"
            issue_url = f"https://issues.redhat.com/browse/{issue_key}"
            summary.append(f"  - [{issue_key}]({issue_url}) → Parent: [{parent_key}]({parent_url})")
    summary.append(f"- **Issues with Epic Links:** {epic_count}")
    summary.append(f"- **Issues with no Epic or Parent:** {no_link_count}")

    return "\n".join(summary)


def generate_report(team_number: str, sprint_name: str, issues: List[Dict[str, Any]],
                   epic_data: Dict[str, Any] = None) -> str:
    """Generate the complete markdown report with hierarchy summary and parent epic details."""
    report = []

    report.append(f"# Sprint {sprint_name} Issues - Team {team_number}")
    report.append("")
    report.append(f"**Total Issues:** {len(issues)}")
    report.append(f"**Generated:** {import_datetime()}")
    report.append("")

    # Get epic information
    epic_info = get_epic_info(issues, epic_data)

    # Add Hierarchy Summary section (first)
    if epic_info and any(info.get('parent_key') for info in epic_info.values()):
        report.append(generate_hierarchy_summary(epic_info))

    # Add Parent Epic Details section (second)
    if epic_info and any(info.get('parent_key') for info in epic_info.values()):
        report.append(generate_parent_epic_details(epic_info))

    # Add Parent Link Summary section (third)
    report.append("## Parent Link Summary")
    report.append("")
    report.append(generate_parent_summary(issues))
    report.append("")

    # Add Report Summary section
    report.append("## Report Summary")
    report.append("")
    epic_count = len([e for e in epic_info.keys()])
    no_epic_count = sum(1 for issue in issues
                       if not issue.get('custom_fields', {}).get('customfield_12311140', {}).get('value'))
    report.append(f"Sprint {sprint_name} for Team {team_number} contains {len(issues)} issues "
                 f"distributed across {epic_count} different epics. "
                 f"{no_epic_count} issues are standalone without epic associations.")
    report.append("")

    # Add detailed sections
    report.append("---")
    report.append("")
    report.append(f"## Detailed Sprint {sprint_name} Issue List with Parent/Epic Links")
    report.append("")
    report.append(f"**Total Issues:** {len(issues)} issues in Sprint {sprint_name} (AIPCC Team {team_number})")
    report.append(f"**Generated:** {import_datetime()}")
    report.append("")
    report.append(format_issue_table(issues))
    report.append("")

    report.append("### Epic Distribution Summary with Parent Links")
    report.append("")
    report.append(generate_epic_summary(issues, epic_info))
    report.append("")

    report.append("---")
    report.append("*Generated from JIRA data for future sprint planning purposes*")
    report.append("")

    return "\n".join(report)


def import_datetime():
    """Import and format current datetime."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Jira sprint parent links report"
    )
    parser.add_argument("team_number", help="Jira team number (e.g., 5800)")
    parser.add_argument("sprint_name", help="Sprint name (e.g., 'Sprint 25')")
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--json-input", "-j",
        help="Path to JSON file with Jira search results (for testing)"
    )

    args = parser.parse_args()

    if args.json_input:
        # Load from file for testing
        with open(args.json_input, 'r') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                # Handle Claude MCP format
                issues_data = json.loads(data[0]['text'])
                issues = issues_data.get('issues', [])
            else:
                issues = data.get('issues', [])
    else:
        print("Error: This script requires --json-input for testing.", file=sys.stderr)
        print("When used as a Claude skill, Claude will execute the Jira search directly.", file=sys.stderr)
        sys.exit(1)

    report = generate_report(args.team_number, args.sprint_name, issues)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
