"""
Custom skillsaw rules for the ODH AI Helpers marketplace (plugins/ layout).
"""

import json
import subprocess
from typing import List

try:
    from src.context import RepositoryContext
    from src.rule import Rule, RuleViolation, Severity
except ImportError:
    from skillsaw import RepositoryContext, Rule, RuleViolation, Severity


class PluginsDocUpToDateRule(Rule):
    """Check that generated marketplace/settings/site data are up-to-date."""

    @property
    def rule_id(self) -> str:
        return "plugins-doc-up-to-date"

    @property
    def description(self) -> str:
        return (
            "docs/data.json, .claude-plugin/marketplace.json and"
            " images/claude/claude-settings.json must be up-to-date with the"
            " plugins/ tree. Run 'make update' to regenerate."
        )

    def default_severity(self) -> Severity:
        return Severity.ERROR

    def check(self, context: RepositoryContext) -> List[RuleViolation]:
        violations = []

        if not context.has_marketplace():
            return violations

        plugins_dir = context.root_path / "plugins"
        if not plugins_dir.exists():
            return violations

        generated = {
            "docs/data.json": context.root_path / "docs" / "data.json",
            ".claude-plugin/marketplace.json": (
                context.root_path / ".claude-plugin" / "marketplace.json"
            ),
            "images/claude/claude-settings.json": (
                context.root_path / "images" / "claude" / "claude-settings.json"
            ),
        }
        scripts = [
            context.root_path / "scripts" / "build-website.py",
            context.root_path / "scripts" / "update_claude_settings.py",
        ]

        try:
            originals = {
                label: (path.read_text() if path.exists() else None)
                for label, path in generated.items()
            }

            for script in scripts:
                if not script.exists():
                    continue
                result = subprocess.run(
                    [str(script)],
                    cwd=str(context.root_path),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    violations.append(
                        self.violation(
                            f"{script.name} failed: {result.stderr.strip()}",
                            file_path=plugins_dir,
                        )
                    )
                    return violations

            for label, path in generated.items():
                if not path.exists():
                    continue
                regenerated = path.read_text()
                if originals[label] != regenerated:
                    if originals[label] is not None:
                        path.write_text(originals[label])
                    violations.append(
                        self.violation(
                            f"{label} is out of sync with the plugins/ tree."
                            " Run 'make update' to regenerate.",
                            file_path=path,
                        )
                    )

        except subprocess.TimeoutExpired:
            violations.append(self.violation("'make update' timed out", file_path=plugins_dir))
        except Exception as e:
            violations.append(
                self.violation(f"Error checking generated files: {e}", file_path=plugins_dir)
            )

        return violations


class MarketplacePluginsUpToDateRule(Rule):
    """Check that marketplace.json lists every plugins/<plugin> directory."""

    @property
    def rule_id(self) -> str:
        return "marketplace-plugins-up-to-date"

    @property
    def description(self) -> str:
        return ".claude-plugin/marketplace.json must include all plugins/ entries"

    def default_severity(self) -> Severity:
        return Severity.ERROR

    def check(self, context: RepositoryContext) -> List[RuleViolation]:
        violations = []

        marketplace_path = context.root_path / ".claude-plugin" / "marketplace.json"
        plugins_dir = context.root_path / "plugins"
        if not marketplace_path.exists() or not plugins_dir.exists():
            return violations

        try:
            with open(marketplace_path, "r") as f:
                marketplace_data = json.load(f)

            if "plugins" not in marketplace_data:
                violations.append(
                    self.violation(
                        "marketplace.json is missing 'plugins' field",
                        file_path=marketplace_path,
                    )
                )
                return violations

            available_plugins = [p.name for p in plugins_dir.iterdir() if p.is_dir()]

            marketplace_plugins = {}
            for plugin in marketplace_data["plugins"]:
                name = plugin.get("name")
                if name:
                    marketplace_plugins[name] = plugin.get("source")

            missing_plugins = set(available_plugins) - set(marketplace_plugins.keys())
            if missing_plugins:
                violations.append(
                    self.violation(
                        "marketplace.json is missing plugins:"
                        f" {', '.join(sorted(missing_plugins))}",
                        file_path=marketplace_path,
                    )
                )

            for plugin_name in available_plugins:
                source_path = marketplace_plugins.get(plugin_name)
                expected_source = f"./plugins/{plugin_name}"
                if source_path is not None and source_path != expected_source:
                    violations.append(
                        self.violation(
                            f"Plugin '{plugin_name}' source path should be"
                            f" '{expected_source}', got '{source_path}'",
                            file_path=marketplace_path,
                        )
                    )

        except json.JSONDecodeError as e:
            violations.append(
                self.violation(f"Invalid JSON in marketplace.json: {e}", file_path=marketplace_path)
            )
        except Exception as e:
            violations.append(
                self.violation(f"Error checking marketplace.json: {e}", file_path=marketplace_path)
            )

        return violations


class PluginsValidationRule(Rule):
    """Validate the plugins/ structure and prevent duplicate tool names."""

    @property
    def rule_id(self) -> str:
        return "tools-yaml-validation"

    @property
    def description(self) -> str:
        return (
            "plugins/ must have valid structure: each plugin has a"
            " .claude-plugin/plugin.json matching its directory, every skill has"
            " a SKILL.md, and no tool name is duplicated across plugins"
        )

    def default_severity(self) -> Severity:
        return Severity.ERROR

    def check(self, context: RepositoryContext) -> List[RuleViolation]:
        violations = []

        plugins_dir = context.root_path / "plugins"
        if not plugins_dir.exists():
            if context.has_marketplace():
                violations.append(
                    self.violation(
                        "plugins/ directory is required for marketplace repos",
                        file_path=plugins_dir,
                    )
                )
            return violations

        validation_script_path = context.root_path / "scripts" / "validate_tools.py"
        if not validation_script_path.exists():
            violations.append(
                self.violation(
                    "scripts/validate_tools.py not found but plugins/ exists",
                    file_path=plugins_dir,
                )
            )
            return violations

        try:
            result = subprocess.run(
                ["python3", str(validation_script_path), str(plugins_dir)],
                cwd=str(context.root_path),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                output = "\n".join(part for part in [result.stdout, result.stderr] if part)
                for line in output.strip().split("\n"):
                    if line.strip().startswith("✗"):
                        error_msg = line.strip()[1:].strip()
                        violations.append(
                            self.violation(
                                f"plugins validation error: {error_msg}",
                                file_path=plugins_dir,
                            )
                        )
                if not violations:
                    violations.append(
                        self.violation(
                            f"plugins validation failed: {output.strip()}",
                            file_path=plugins_dir,
                        )
                    )

        except subprocess.TimeoutExpired:
            violations.append(
                self.violation("plugins validation script timed out", file_path=plugins_dir)
            )
        except Exception as e:
            violations.append(
                self.violation(f"Error running plugins validation: {e}", file_path=plugins_dir)
            )

        return violations
