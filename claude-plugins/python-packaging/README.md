# Python Packaging Plugin

A comprehensive Claude Code plugin that provides tools, skills, and specialized agents for Python package management, build analysis, and wheel building strategies.

## Overview

The Python Packaging plugin helps developers and DevOps engineers make informed decisions about Python package building, dependency management, and wheel distribution strategies. It provides both automated skills for PyPI metadata analysis and specialized investigator agents for deep repository analysis. The plugin can assess build complexity, identify compilation requirements, investigate source code repositories, and recommend optimal packaging approaches.

## Features

### 🔍 Build Complexity Analysis
- Evaluate whether packages require compilation (C/C++/Rust/Fortran)
- Assess build difficulty with numerical scoring
- Identify platform-specific requirements
- Analyze wheel availability and distribution gaps

### 📊 PyPI Metadata Inspection
- Comprehensive package metadata analysis
- Dependency tree evaluation
- License and classifier information
- Distribution type analysis (wheels vs source)

### 🛠️ Wheel Building Recommendations
- Optimal build strategies for different package types
- Platform-specific guidance
- Resource and time estimation
- Tool requirement identification

### 🕵️ Repository Investigation
- Comprehensive source code repository analysis
- Build system detection (setup.py, pyproject.toml, CMake, Bazel, etc.)
- CI/CD pipeline examination (GitHub Actions, Travis, GitLab CI, etc.)
- Documentation mining for build instructions
- Dependency tree analysis from source

## Skills

### Complexity Analysis
**Skill Name:** `complexity`

Analyzes Python package build complexity by inspecting PyPI metadata. Automatically triggered when asking about package build requirements, compilation needs, or wheel building strategies.

**Example Usage:**
- "How complex is building PyTorch from source?"
- "Does numpy require compilation?"
- "What wheels are available for tensorflow?"
- "Should I build scikit-learn or use existing wheels?"

## Agents

### Python Packaging Investigator
**Agent Name:** `python-packaging-investigator`

A specialized investigator agent that thoroughly analyzes Git repositories to understand how Python packages can be built from source. Perfect for evaluating unfamiliar packages or planning build strategies.

**Capabilities:**
- **Repository Analysis**: Clones and examines Git repositories for build configuration
- **Build System Detection**: Identifies setup.py, pyproject.toml, CMake, Bazel, Makefile, and other build systems
- **CI/CD Investigation**: Analyzes GitHub Actions, Travis CI, GitLab CI, and other automation workflows
- **Documentation Mining**: Extracts build instructions from README, INSTALL, and CONTRIBUTING files
- **Complexity Integration**: Combines repository analysis with PyPI complexity assessment

**Example Usage:**
- "Investigate how to build https://github.com/user/package from source"
- "Analyze the build system for this repository: [URL]"
- "How do I set up the build environment for [repository]?"
- "What dependencies does this package need for compilation?"

**Workflow:**
1. Prompts for Git repository URL
2. Clones and analyzes repository structure
3. Detects build systems and configuration files
4. Examines CI/CD processes and documentation
5. Runs complexity analysis if package is on PyPI
6. Provides comprehensive build guidance and recommendations

## Installation

### Via Claude Code Plugin Marketplace

1. Add the AI Helpers marketplace:
   ```bash
   /plugin marketplace add git@gitlab.com:redhat/rhel-ai/core/ai-helpers.git
   ```

2. Install the python-packaging plugin:
   ```bash
   /plugin install python-packaging@odh-ai-helpers
   ```

### Manual Installation

1. Clone the AI Helpers repository:
   ```bash
   git clone git@gitlab.com:redhat/rhel-ai/core/ai-helpers.git
   ```

2. Link the plugin to your Claude directory:
   ```bash
   ln -sf $(pwd)/ai-helpers/claude-plugins/python-packaging ~/.claude/plugins/
   ```

## Dependencies

### System Requirements
- **Python 3.8+**: Required for the PyPI inspection script
- **urllib3**: Standard library (no additional installation needed)
