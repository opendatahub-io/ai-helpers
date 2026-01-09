#!/usr/bin/env python3
"""
Skill activation hook for Claude Code.
Analyzes user prompts and suggests relevant skills based on trigger patterns.
"""

import sys
import json
import re
from pathlib import Path


class SkillActivationChecker:
    """Checks user prompts for skill activation triggers.

    Analyzes user prompts against skill rules to determine which skills
    should be suggested based on keyword and intent pattern matching.

    Attributes:
        rules_path (Path): Path to the skill-rules.json file.
        rules (dict): Loaded skill rules configuration.
    """

    def __init__(self, rules_path: Path):
        """Initialize the skill activation checker.

        Args:
            rules_path (Path): Path to the skill-rules.json file.
        """
        self.rules_path = rules_path
        self.rules = self._load_rules()

    def _load_rules(self) -> dict:
        """Load skill rules from JSON file.

        Returns:
            dict: Parsed skill rules configuration.

        Raises:
            SystemExit: If file not found or JSON parsing fails.
        """
        try:
            with open(self.rules_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: skill-rules.json not found at {self.rules_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing skill-rules.json: {e}", file=sys.stderr)
            sys.exit(1)

    def check_prompt(self, prompt: str) -> list[dict]:
        """Check prompt against all skill rules and return matches.

        Args:
            prompt (str): User prompt text to analyze.

        Returns:
            list[dict]: List of matched skills with metadata:
                - name (str): Skill name
                - match_type (str): Either 'keyword' or 'intent'
                - config (dict): Skill configuration from rules
        """
        prompt_lower = prompt.lower()
        matched_skills = []

        skills = self.rules.get('skills', {})

        for skill_name, config in skills.items():
            triggers = config.get('promptTriggers', {})

            # Check keyword triggers
            keywords = triggers.get('keywords', [])
            if keywords and any(kw.lower() in prompt_lower for kw in keywords):
                matched_skills.append({
                    'name': skill_name,
                    'match_type': 'keyword',
                    'config': config
                })
                continue

            # Check intent pattern triggers
            intent_patterns = triggers.get('intentPatterns', [])
            if intent_patterns:
                for pattern in intent_patterns:
                    try:
                        if re.search(pattern, prompt, re.IGNORECASE):
                            matched_skills.append({
                                'name': skill_name,
                                'match_type': 'intent',
                                'config': config
                            })
                            break
                    except re.error as e:
                        print(f"Warning: Invalid regex pattern '{pattern}': {e}", file=sys.stderr)

        return matched_skills

    def format_output(self, matched_skills: list[dict]) -> str:
        """Format matched skills into readable output.

        Args:
            matched_skills (list[dict]): List of matched skills from check_prompt.

        Returns:
            str: Formatted output string with skill suggestions grouped by priority.
                 Empty string if no matches.
        """
        if not matched_skills:
            return ""

        output = []
        output.append("━" * 42)
        output.append("🎯 SKILL ACTIVATION CHECK")
        output.append("━" * 42)
        output.append("")

        # Group by priority
        critical = [s for s in matched_skills if s['config'].get('priority') == 'critical']
        high = [s for s in matched_skills if s['config'].get('priority') == 'high']
        medium = [s for s in matched_skills if s['config'].get('priority') == 'medium']
        low = [s for s in matched_skills if s['config'].get('priority') == 'low']

        if critical:
            output.append("⚠️  CRITICAL SKILLS (REQUIRED):")
            for skill in critical:
                output.append(f"  → {skill['name']}")
            output.append("")

        if high:
            output.append("📚 RECOMMENDED SKILLS:")
            for skill in high:
                output.append(f"  → {skill['name']}")
            output.append("")

        if medium:
            output.append("💡 SUGGESTED SKILLS:")
            for skill in medium:
                output.append(f"  → {skill['name']}")
            output.append("")

        if low:
            output.append("📌 OPTIONAL SKILLS:")
            for skill in low:
                output.append(f"  → {skill['name']}")
            output.append("")

        output.append("ACTION: Use Skill tool BEFORE responding")
        output.append("━" * 42)

        return "\n".join(output)


def main():
    """Main entry point for the skill activation hook.

    Reads JSON input from stdin containing user prompt, checks for skill matches,
    and outputs formatted suggestions if any skills are triggered.

    Stdin Input:
        JSON object with 'prompt' field containing user's message.

    Environment Variables:
        CLAUDE_PROJECT_DIR: Path to project directory (defaults to ~/project).

    Exits:
        0: Success (with or without matches)
        1: Error (invalid JSON, missing rules file, etc.)
    """
    try:
        # Read input from stdin
        input_data = sys.stdin.read()
        data = json.loads(input_data)
        prompt = data.get('prompt', '')

        # Get project directory
        import os
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.path.expanduser('~/project'))
        rules_path = Path(project_dir) / '.claude' / 'skills' / 'skill-rules.json'

        # Check for skill matches
        checker = SkillActivationChecker(rules_path)
        matched_skills = checker.check_prompt(prompt)

        # Output results
        if matched_skills:
            output = checker.format_output(matched_skills)
            print(output)

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Error parsing input JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error in skill_activation_prompt hook: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
