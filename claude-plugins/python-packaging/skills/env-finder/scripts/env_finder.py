#!/usr/bin/env python3
"""
Environment Variables Investigation Script for Python Wheel Building

This script analyzes Python projects to discover environment variables
that can be set during wheel building. It examines various build
configuration files and extracts environment variable usage.
"""

import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class EnvVariable:
    """Represents a discovered environment variable"""

    name: str
    description: str
    var_type: str
    default_value: Optional[str]
    source_file: str
    line_number: Optional[int]
    usage_context: str


class EnvironmentVariableInvestigator:
    """Main class for investigating environment variables in Python projects"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.variables: Dict[str, EnvVariable] = {}

        # Common environment variable patterns
        self.env_patterns = [
            # os.environ patterns
            (
                r'os\.environ\.get\([\'"]([A-Z_][A-Z0-9_]*)[\'"](?:,\s*[\'"]([^\'"]*)[\'"]\s*)?\)',
                "os.environ.get",
            ),
            (r'os\.environ\[[\'"]([A-Z_][A-Z0-9_]*)[\'"]?\]', "os.environ access"),
            (
                r'os\.getenv\([\'"]([A-Z_][A-Z0-9_]*)[\'"](?:,\s*[\'"]([^\'"]*)[\'"]\s*)?\)',
                "os.getenv",
            ),
            # CMake environment variable patterns
            (r"\$ENV\{([A-Z_][A-Z0-9_]*)\}", "CMake ENV"),
            # Shell/Make patterns - more restrictive to avoid false positives
            (r"\$\{([A-Z_][A-Z0-9_]*)\}", "Shell variable"),
            # Only match shell variables in specific contexts (not in Python strings)
            (
                r"(?:^|[^'\"])(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=",
                "Variable assignment",
            ),
            # Match environment variable usage in shell scripts/makefiles
            (
                r"(?:^|\s)\$([A-Z_][A-Z0-9_]*)(?=\s|$|[^A-Za-z0-9_])",
                "Shell variable reference",
            ),
        ]

        # Known environment variables with descriptions
        self.known_vars = {
            "CC": "C compiler command",
            "CXX": "C++ compiler command",
            "CFLAGS": "C compiler flags",
            "CXXFLAGS": "C++ compiler flags",
            "LDFLAGS": "Linker flags",
            "PREFIX": "Installation prefix",
            "DESTDIR": "Destination directory for installation",
            "PYTHON": "Python interpreter path",
            "PYTHON_INCLUDE_DIR": "Python headers directory",
            "PYTHON_LIBRARY": "Python library path",
            "PKG_CONFIG_PATH": "pkg-config search path",
            "LIBRARY_PATH": "Library search path",
            "LD_LIBRARY_PATH": "Runtime library search path",
            "PATH": "Executable search path",
            "MAKEFLAGS": "Make command flags",
            "JOBS": "Number of parallel build jobs",
            "BUILD_TYPE": "Build configuration type",
        }

    def validate_git_repository(self) -> bool:
        """Validate that the target is a git repository"""
        git_dir = self.project_path / ".git"
        return git_dir.exists() and (git_dir.is_dir() or git_dir.is_file())

    def find_build_files(self) -> List[Path]:
        """Find all potential build configuration files"""
        build_patterns = [
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
            "CMakeLists.txt",
            "**/CMakeLists.txt",
            "configure.ac",
            "configure.in",
            "Makefile",
            "makefile",
            "*.mk",
            "build.py",
            "conda.yaml",
            "environment.yml",
        ]

        files = []
        for pattern in build_patterns:
            if "*" in pattern:
                files.extend(self.project_path.glob(f"**/{pattern}"))
            else:
                file_path = self.project_path / pattern
                if file_path.exists():
                    files.append(file_path)

        return files

    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for environment variables"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                self._analyze_line(line, file_path, line_num)

        except (IOError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    def _analyze_line(self, line: str, file_path: Path, line_num: int) -> None:
        """Analyze a single line for environment variable patterns"""
        # Skip lines that are clearly Python code with dunder variables
        if self._is_python_dunder_line(line):
            return

        # Skip lines that look like Python imports or function definitions
        if self._is_python_code_line(line):
            return

        for pattern, context in self.env_patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                var_name = match.group(1)
                default_value = match.group(2) if match.lastindex >= 2 else None

                # Filter out obvious false positives
                if self._is_valid_env_var(var_name) and self._is_valid_context(
                    line, var_name, context
                ):
                    self._add_variable(
                        var_name=var_name,
                        file_path=file_path,
                        line_num=line_num,
                        context=context,
                        default_value=default_value,
                        line_content=line.strip(),
                    )

    def _is_python_dunder_line(self, line: str) -> bool:
        """Check if line contains Python dunder variables"""
        return bool(re.search(r"__\w+__", line))

    def _is_python_code_line(self, line: str) -> bool:
        """Check if line looks like Python code that might contain false positives"""
        stripped = line.strip()

        # Skip Python imports, function definitions, class definitions
        if any(
            stripped.startswith(prefix)
            for prefix in ["import ", "from ", "def ", "class ", "if __name__", "@"]
        ):
            return True

        # Skip lines with Python-specific patterns
        python_patterns = [
            r"^\s*#.*",  # Comments
            r'.*\.py[co]?["\']',  # Python file references
            r".*setuptools.*",  # setuptools imports/usage
            r".*distutils.*",  # distutils imports/usage
        ]

        return any(re.match(pattern, stripped) for pattern in python_patterns)

    def _is_valid_context(self, line: str, var_name: str, context: str) -> bool:
        """Check if the variable appears in a valid environment variable context"""
        # Always allow os.environ and os.getenv contexts
        if context in ["os.environ.get", "os.environ access", "os.getenv"]:
            return True

        # For shell/make contexts, be more restrictive
        if context in [
            "Shell variable",
            "Shell variable reference",
            "Variable assignment",
        ]:
            # Skip if it appears to be in a Python string
            if re.search(
                r"""['"]{1,3}.*""" + re.escape(var_name) + r""".*['"]{1,3}""", line
            ):
                return False

            # Skip if it's in a Python comment
            if "#" in line and line.index("#") < line.find(var_name):
                comment_part = line[line.index("#") :]
                if var_name in comment_part:
                    return False

        return True

    def _is_valid_env_var(self, var_name: str) -> bool:
        """Check if a variable name looks like a valid environment variable"""
        # Must be all uppercase with underscores
        if not re.match(r"^[A-Z_][A-Z0-9_]*$", var_name):
            return False

        # Filter out Python dunder variables (start and end with double underscores)
        if var_name.startswith("__") and var_name.endswith("__"):
            return False

        # Filter out variables that are just underscores
        if re.match(r"^_+$", var_name):
            return False

        # Filter out single character variables (except well-known ones)
        if len(var_name) == 1 and var_name not in {"C", "F", "H", "P", "X", "Y", "Z"}:
            return False

        # Filter out common false positives
        false_positives = {
            "TRUE",
            "FALSE",
            "ON",
            "OFF",
            "YES",
            "NO",
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "HEAD",
            "ARGS",
            "KWARGS",
            "SELF",
            "CLS",
            "SUPER",
            "TYPE",
            "CLASS",
            "OBJECT",
            "DICT",
            "LIST",
            "TUPLE",
            "SET",
            "STR",
            "INT",
            "FLOAT",
            "BOOL",
            "NONE",
            "INIT",
            "NEW",
            "CALL",
            "REPR",
            "LEN",
            "ITER",
            "NEXT",
            "ENTER",
            "EXIT",
            "NAME",
            "MAIN",
            "FILE",
            "DOC",
            "MODULE",
            "PACKAGE",
            "SPEC",
            "LOADER",
            "CACHED",
            "PATH",  # Only when it's clearly not an env var
            "ENV",  # CMake keyword, not an env var
        }

        return var_name not in false_positives and len(var_name) >= 2

    def _add_variable(
        self,
        var_name: str,
        file_path: Path,
        line_num: int,
        context: str,
        default_value: Optional[str],
        line_content: str,
    ) -> None:
        """Add a discovered environment variable"""

        # Determine variable type and description
        description = self.known_vars.get(
            var_name, self._infer_description(var_name, line_content)
        )
        var_type = self._infer_type(var_name, default_value, line_content)

        # If we already have this variable, update with more information
        if var_name in self.variables:
            existing = self.variables[var_name]
            # Keep the most descriptive information
            if len(description) > len(existing.description):
                existing.description = description
            if not existing.default_value and default_value:
                existing.default_value = default_value
        else:
            self.variables[var_name] = EnvVariable(
                name=var_name,
                description=description,
                var_type=var_type,
                default_value=default_value,
                source_file=str(file_path.relative_to(self.project_path)),
                line_number=line_num,
                usage_context=context,
            )

    def _infer_description(self, var_name: str, line_content: str) -> str:
        """Infer description from variable name and context"""

        # Common patterns in variable names
        name_patterns = {
            r".*PATH.*": "Path configuration variable",
            r".*DIR.*": "Directory path variable",
            r".*HOME.*": "Home directory path",
            r".*ROOT.*": "Root directory path",
            r".*PREFIX.*": "Installation prefix path",
            r".*FLAGS.*": "Compilation or configuration flags",
            r".*OPTS.*": "Options or settings",
            r".*ENABLE.*": "Feature enable flag",
            r".*DISABLE.*": "Feature disable flag",
            r".*WITH.*": "Include/use feature flag",
            r".*WITHOUT.*": "Exclude feature flag",
            r".*VERSION.*": "Version specification",
            r".*URL.*": "URL configuration",
            r".*HOST.*": "Host configuration",
            r".*PORT.*": "Port configuration",
            r".*USER.*": "User configuration",
            r".*PASS.*": "Password configuration",
            r".*KEY.*": "Key or credential",
            r".*TOKEN.*": "Authentication token",
            r".*LIB.*": "Library configuration",
            r".*INCLUDE.*": "Include path or flag",
        }

        for pattern, desc in name_patterns.items():
            if re.match(pattern, var_name, re.IGNORECASE):
                return desc

        return f"Environment variable {var_name}"

    def _infer_type(
        self, var_name: str, default_value: Optional[str], line_content: str
    ) -> str:
        """Infer the expected type of the variable"""

        # Check default value for type hints
        if default_value:
            if default_value.lower() in ("true", "false", "1", "0"):
                return "boolean"
            elif default_value.isdigit():
                return "number"
            elif "/" in default_value or "\\" in default_value:
                return "path"
            else:
                return "string"

        # Infer from variable name
        if any(
            word in var_name.lower()
            for word in ["path", "dir", "home", "root", "prefix"]
        ):
            return "path"
        elif any(
            word in var_name.lower()
            for word in ["enable", "disable", "with", "without"]
        ):
            return "boolean"
        elif any(word in var_name.lower() for word in ["port", "count", "num", "jobs"]):
            return "number"
        else:
            return "string"

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a report of discovered environment variables"""

        if output_format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()

    def _generate_json_report(self) -> str:
        """Generate JSON format report"""
        data = {
            "project_path": str(self.project_path),
            "variables_found": len(self.variables),
            "variables": {
                name: {
                    "description": var.description,
                    "type": var.var_type,
                    "default_value": var.default_value,
                    "source_file": var.source_file,
                    "line_number": var.line_number,
                    "usage_context": var.usage_context,
                }
                for name, var in sorted(self.variables.items())
            },
        }
        return json.dumps(data, indent=2)

    def _generate_text_report(self) -> str:
        """Generate human-readable text report"""
        if not self.variables:
            return "No environment variables found in the project."

        report = f"Environment Variables Found in {self.project_path.name}\n"
        report += "=" * (len(report) - 1) + "\n\n"
        report += f"Total variables discovered: {len(self.variables)}\n\n"

        # Group by category
        categories = {}
        for var in self.variables.values():
            category = self._categorize_variable(var.name)
            if category not in categories:
                categories[category] = []
            categories[category].append(var)

        for category, vars_in_category in sorted(categories.items()):
            report += f"{category}\n"
            report += "-" * len(category) + "\n"

            for var in sorted(vars_in_category, key=lambda x: x.name):
                report += f"  {var.name}\n"
                report += f"    Description: {var.description}\n"
                report += f"    Type: {var.var_type}\n"
                if var.default_value:
                    report += f"    Default: {var.default_value}\n"
                report += f"    Source: {var.source_file}:{var.line_number}\n"
                report += f"    Context: {var.usage_context}\n"
                report += "\n"

        return report

    def _categorize_variable(self, var_name: str) -> str:
        """Categorize a variable by its purpose"""
        name_lower = var_name.lower()

        if any(
            word in name_lower
            for word in ["cc", "cxx", "cflags", "cxxflags", "ldflags"]
        ):
            return "Compiler and Linker Variables"
        elif any(
            word in name_lower for word in ["path", "dir", "home", "root", "prefix"]
        ):
            return "Path Configuration Variables"
        elif any(
            word in name_lower for word in ["enable", "disable", "with", "without"]
        ):
            return "Feature Control Variables"
        elif any(word in name_lower for word in ["python", "pip", "setuptools"]):
            return "Python-Specific Variables"
        elif any(word in name_lower for word in ["cmake", "make", "build"]):
            return "Build System Variables"
        else:
            return "General Variables"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Investigate environment variables in Python projects"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Path to the Python project (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    investigator = EnvironmentVariableInvestigator(args.project_path)

    # Validate git repository
    if not investigator.validate_git_repository():
        print(
            "Error: This is not a git repository. Please provide a cloned git repository.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.verbose:
        print(f"Analyzing project: {investigator.project_path}")

    # Find and analyze build files
    build_files = investigator.find_build_files()

    if args.verbose:
        print(f"Found {len(build_files)} build configuration files")
        for file_path in build_files:
            print(f"  - {file_path.relative_to(investigator.project_path)}")
        print()

    if not build_files:
        print("Warning: No build configuration files found", file=sys.stderr)

    # Analyze each file
    for file_path in build_files:
        if args.verbose:
            print(f"Analyzing {file_path.relative_to(investigator.project_path)}...")
        investigator.analyze_file(file_path)

    # Generate and display report
    output_format = "json" if args.json else "text"
    report = investigator.generate_report(output_format)
    print(report)


if __name__ == "__main__":
    main()
