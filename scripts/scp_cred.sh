#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Copy Credentials to Remote Host
# =============================================================================
# Copies gcloud, anthropic, and git configuration to a remote host for use
# with dev containers that require these credentials.
#
# Usage:
#   ./scp_cred.sh <remote-host>
#
# Arguments:
#   remote-host  SSH host to copy credentials to (must be in ~/.ssh/config)
#
# Examples:
#   ./scp_cred.sh my-remote-server
# =============================================================================

if [ $# -ne 1 ]; then
    echo "Error: Missing remote host argument"
    echo ""
    echo "Usage: $0 <remote-host>"
    exit 1
fi

REMOTE_HOST="$1"

echo "Copying credentials to $REMOTE_HOST..."
echo ""

# Copy gcloud configuration
if [ -d ~/.config/gcloud ]; then
    echo "→ Copying gcloud configuration..."
    scp -r ~/.config/gcloud "$REMOTE_HOST:~/.config/" && echo "  ✓ gcloud config copied"
else
    echo "  ⚠ Warning: ~/.config/gcloud not found, skipping"
fi

# Copy anthropic configuration
if [ -d ~/.anthropic ]; then
    echo "→ Copying anthropic configuration..."
    scp -r ~/.anthropic "$REMOTE_HOST:~/" && echo "  ✓ anthropic config copied"
else
    echo "  ⚠ Warning: ~/.anthropic not found, skipping"
fi

# Copy gitconfig
if [ -f ~/.gitconfig ]; then
    echo "→ Copying git configuration..."
    scp ~/.gitconfig "$REMOTE_HOST:~/" && echo "  ✓ gitconfig copied"
else
    echo "  ⚠ Warning: ~/.gitconfig not found, skipping"
fi

echo ""
echo "============================================"
echo "✓ Credentials copied to $REMOTE_HOST"
echo "============================================"
echo ""
echo "You can now connect to the remote host and open the dev container."
echo "Claude Code will automatically authenticate with Vertex AI."
