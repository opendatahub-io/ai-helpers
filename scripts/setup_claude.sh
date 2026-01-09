#!/usr/bin/env bash
set -euo pipefail

# Verify gcloud credentials are mounted and working
if ! gcloud auth application-default print-access-token &>/dev/null; then
    echo "ERROR: GCloud credentials not found or expired."
    echo "On your HOST machine, run: gcloud auth application-default login"
    echo "Then rebuild the container to mount the credentials."
    exit 1
fi

# Install Claude Code using native installer
curl -fsSL https://claude.ai/install.sh | bash
