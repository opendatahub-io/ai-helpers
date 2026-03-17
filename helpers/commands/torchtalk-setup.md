---
description: Install and configure TorchTalk MCP server for PyTorch cross-language analysis
---

## Name
odh-ai-helpers:torchtalk-setup

## Synopsis
```text
/torchtalk:setup
```

## Description
The `torchtalk:setup` command guides you through the complete installation and configuration of the TorchTalk MCP server, which enables cross-language binding analysis for PyTorch codebases (Python/C++/CUDA). This command:

- Checks for and installs required dependencies (Python 3.10+, pip)
- Clones and builds TorchTalk from source
- Locates or clones PyTorch source code
- Configures TorchTalk with the PyTorch source path
- Registers the MCP server with Claude Code at user scope
- Verifies the complete setup

After setup, you can use `/torchtalk:trace` and the full suite of TorchTalk MCP tools across all Claude Code sessions.

## Implementation

### Phase 1: Check Prerequisites

#### 1.1 Verify Python Version

```bash
python3 --version
```

**Minimum required:** Python 3.10

**If Python is too old or missing:**
```text
Python 3.10+ is required for TorchTalk.

Install or upgrade Python:
- macOS: brew install python@3.12
- Ubuntu/Debian: sudo apt install python3.12
- Fedora/RHEL: sudo dnf install python3.12
```

#### 1.2 Verify pip

```bash
python3 -m pip --version
```

If pip is missing, provide platform-specific installation instructions.

#### 1.3 Check for Existing TorchTalk Installation

```bash
which torchtalk
```

If torchtalk is found:
- Run `torchtalk status` to show current configuration
- Ask the user if they want to:
  1. Reconfigure the existing installation
  2. Reinstall from scratch
  3. Exit setup

### Phase 2: Install TorchTalk

#### 2.1 Determine Installation Location

Ask the user where they want to install TorchTalk:

```text
Where would you like to install TorchTalk?

1. ~/src/torchtalk (recommended)
2. ~/.local/share/torchtalk
3. Custom path
```

Store the chosen directory as `$TORCHTALK_DIR`.

#### 2.2 Clone the Repository

```bash
mkdir -p "$(dirname "$TORCHTALK_DIR")"
git clone https://github.com/adabeyta/torchtalk.git "$TORCHTALK_DIR"
```

**Handle errors:**
- Directory already exists: Ask to use existing or remove and re-clone
- Network issues: Provide troubleshooting steps
- Permission issues: Suggest a different directory

#### 2.3 Install from Source

```bash
cd "$TORCHTALK_DIR"
pip install -e .
```

**Verify installation:**
```bash
torchtalk --help
```

**If install fails:**
- Check Python version meets minimum requirements
- Check for missing system dependencies (libclang may need system packages)
- Display error message and suggest checking the TorchTalk README

**If libclang fails to install:**
```text
libclang requires the clang development libraries.

Install:
- macOS: xcode-select --install (usually already present)
- Ubuntu/Debian: sudo apt install libclang-dev
- Fedora/RHEL: sudo dnf install clang-devel
```

### Phase 3: Locate PyTorch Source

#### 3.1 Check for Existing PyTorch Source

Search common locations:

```bash
echo "$PYTORCH_SOURCE"
ls -d ~/pytorch ~/src/pytorch /myworkspace/pytorch 2>/dev/null
```

If PyTorch source is found, confirm with the user:
```text
Found PyTorch source at: /path/to/pytorch

Is this the correct PyTorch source directory? (y/n)
```

#### 3.2 If Not Found, Ask the User

```text
PyTorch source code is required for TorchTalk to index bindings.

Options:
1. Enter the path to an existing PyTorch checkout
2. Clone PyTorch now (requires ~2GB disk space, takes a few minutes)
3. Exit setup and clone manually
```

**If cloning:**
```bash
git clone https://github.com/pytorch/pytorch "$PYTORCH_CLONE_DIR"
```

Store the PyTorch path as `$PYTORCH_SOURCE`.

#### 3.3 Validate PyTorch Source

Run checks separately so users get actionable error messages:

```bash
test -d "$PYTORCH_SOURCE/torch"
```

If the `torch/` directory is missing:
```text
No 'torch/' directory found — does not appear to be a PyTorch checkout.
Please verify the path and try again.
```

```bash
test -f "$PYTORCH_SOURCE/aten/src/ATen/native/native_functions.yaml"
```

If `native_functions.yaml` is missing:
```text
native_functions.yaml not found (required for operator indexing).
The PyTorch checkout may be incomplete or too old.
Consider running: cd "$PYTORCH_SOURCE" && git pull
```

These checks mirror TorchTalk's `validate_pytorch_path()` which validates both the `torch/` directory and `native_functions.yaml`.

### Phase 4: Configure TorchTalk

#### 4.1 Run TorchTalk Init

```bash
torchtalk init --pytorch-source "$PYTORCH_SOURCE"
```

This writes the PyTorch path to `~/.config/torchtalk/config.toml` so future runs need no arguments.

**Verify configuration:**
```bash
torchtalk status
```

Confirm the output shows:
- Config file exists
- PyTorch source is valid
- Status is Ready

#### 4.2 Register MCP Server with Claude Code

```bash
claude mcp add torchtalk -s user -- torchtalk mcp-serve
```

This registers TorchTalk at user scope, making it available across all Claude Code sessions regardless of working directory.

**If `claude` command is not found:**
```text
The Claude Code CLI is required to register MCP servers.

If you're running this from within Claude Code, the registration
may need to be done from a terminal. Copy and run:

  claude mcp add torchtalk -s user -- torchtalk mcp-serve
```

### Phase 5: Verify Setup

Run validation checks to ensure everything is configured correctly:

```bash
torchtalk status
timeout 5 torchtalk mcp-serve 2>&1 || true
```

**Display summary:**
```text
Setup Complete!
===============

  TorchTalk installed at:  $TORCHTALK_DIR
  PyTorch source:          $PYTORCH_SOURCE
  Config file:             ~/.config/torchtalk/config.toml
  MCP server:              Registered at user scope

Next Steps:
-----------

1. Restart Claude Code to activate the MCP server

2. Verify MCP tools are available:
   Run: mcp__torchtalk__get_status

3. Trace your first operator:
   /torchtalk:trace matmul

Optional - Build PyTorch for full call graph support:
   cd $PYTORCH_SOURCE && python setup.py develop

Available Commands:
-------------------
- /torchtalk:trace <function> [focus]  -- Trace binding chains
- The TorchTalk Analyzer skill handles broader questions like
  "How does nn.Linear work?" or "What breaks if I change gemm?"

Documentation:
--------------
- TorchTalk: https://github.com/adabeyta/torchtalk
```

### Phase 6: Optional Call Graph Setup

After the main setup is complete, inform the user about optional advanced features:

```text
Optional: C++ Call Graph Support
================================

TorchTalk can analyze C++ function call relationships (impact analysis,
caller/callee tracking) if PyTorch has been built at least once.

This generates compile_commands.json which TorchTalk uses for
libclang-based static analysis.

Would you like to:
1. Skip for now (you can build later)
2. Learn how to build PyTorch
```

If the user wants build instructions:
```text
Building PyTorch (one-time, takes 30-60 minutes):

  cd $PYTORCH_SOURCE
  python setup.py develop

After building, the call graph features (impact, calls, called_by)
will be automatically available on the next Claude Code session.
```

Check if `compile_commands.json` already exists:
```bash
test -f "$PYTORCH_SOURCE/build/compile_commands.json" && echo "found" || echo "not found"
```

If found: `compile_commands.json already exists. Call graph features are available.`

## Return Value
- **Success**: Installation path, config file location, MCP server registration confirmation, and summary of next steps
- **Partial Success**: List of completed and failed steps with instructions to complete remaining setup manually
- **Error**: Detailed error message, step where failure occurred, and troubleshooting suggestions

## Examples

1. **Fresh install with existing PyTorch source**:
   ```text
   /torchtalk:setup

   > Python 3.12.1 detected
   > Installing TorchTalk to ~/src/torchtalk...
   > Found PyTorch source at ~/pytorch
   > Running torchtalk init...
   > Registering MCP server...

   Setup complete! Restart Claude Code to activate.
   ```

2. **Fresh install, clone everything**:
   ```text
   /torchtalk:setup

   > Python 3.11.5 detected
   > Installing TorchTalk to ~/src/torchtalk...
   > Cloning PyTorch to ~/src/pytorch...
   > Running torchtalk init...
   > Registering MCP server...

   Setup complete! Restart Claude Code to activate.
   ```

3. **Reconfigure existing installation**:
   ```text
   /torchtalk:setup

   > TorchTalk already installed at ~/src/torchtalk
   > Reconfigure? yes
   > Updating PyTorch source path...
   > Re-registering MCP server...

   Reconfiguration complete!
   ```

## Error Handling

### libclang Installation Failure

**Scenario:** `pip install -e .` fails on the libclang dependency.

**Action:**
```text
libclang failed to install. This is usually a missing system package.

Install the clang development libraries:
- macOS: xcode-select --install
- Ubuntu/Debian: sudo apt install libclang-dev
- Fedora/RHEL: sudo dnf install clang-devel

Then retry: pip install -e .
```

### PyTorch Source Too Old or Incomplete

**Scenario:** The PyTorch checkout is missing expected files.

**Action:**
```text
The PyTorch source may be incomplete or too old.

Expected files not found:
- aten/src/ATen/native/native_functions.yaml

Try updating your PyTorch checkout:
  cd $PYTORCH_SOURCE && git pull

Or clone a fresh copy:
  git clone https://github.com/pytorch/pytorch
```

### MCP Server Registration Failure

**Scenario:** `claude mcp add` command fails.

**Action:**
```text
Failed to register MCP server with Claude Code.

You can register manually by running in a terminal:
  claude mcp add torchtalk -s user -- torchtalk mcp-serve

Or add to ~/.claude.json manually:
  {
    "mcpServers": {
      "torchtalk": {
        "command": "torchtalk",
        "args": ["mcp-serve"]
      }
    }
  }
```

## See Also

- [TorchTalk Repository](https://github.com/adabeyta/torchtalk)
- [PyTorch Source](https://github.com/pytorch/pytorch)
- `/torchtalk:trace` - Trace PyTorch function binding chains
- TorchTalk Analyzer skill - Full MCP tools reference

## Arguments
- This command takes no arguments. All configuration is collected interactively.
