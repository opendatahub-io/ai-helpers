#!/bin/bash
# Shallow clone a git repository to a temporary directory
# Usage: ./shallow-clone.sh <repo_url> [branch_or_tag]
# Returns: Path to the cloned repository

repo_url="$1"
ref="${2:-HEAD}"

# Create temporary directory
tmp_dir=$(mktemp -d -t shallow-clone-XXXXXX)

echo "Cloning $repo_url (shallow, ref: $ref) to $tmp_dir..." >&2

# Perform shallow clone
if [ "$ref" = "HEAD" ]; then
    git clone --depth 1 "$repo_url" "$tmp_dir/repo" 2>&1 | grep -v "^Cloning into"
else
    git clone --depth 1 --branch "$ref" "$repo_url" "$tmp_dir/repo" 2>&1 | grep -v "^Cloning into"
fi

if [ -d "$tmp_dir/repo/.git" ]; then
    echo "$tmp_dir/repo"
else
    echo "Error: Failed to clone repository" >&2
    rm -rf "$tmp_dir"
    exit 1
fi
