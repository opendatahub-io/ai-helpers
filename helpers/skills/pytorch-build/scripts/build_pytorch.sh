#!/usr/bin/env bash
set -euo pipefail

# Activate virtual environment from /root/.venv
source ${HOME}/.venv/bin/activate

cd pytorch

git submodule sync
git submodule update --init --recursive --force

uv pip install --no-build-isolation -v -e .

echo "PyTorch built successfully"