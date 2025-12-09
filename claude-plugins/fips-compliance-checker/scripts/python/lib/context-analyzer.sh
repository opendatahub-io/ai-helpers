#!/bin/bash
# Context Analysis Library for FIPS Compliance Scanner
# Provides heuristics for determining file type and production likelihood

# Check if a file is a test file based on path and filename
# Returns: 0 (true) if test file, 1 (false) otherwise
is_test_file() {
    local file_path="$1"

    # Check path components
    if [[ "$file_path" =~ (^|/)(tests?|testing|__tests__|spec|specs)/ ]]; then
        return 0
    fi

    # Check filename patterns
    if [[ "$file_path" =~ test_.*\.py$ ]] || \
       [[ "$file_path" =~ .*_test\.py$ ]] || \
       [[ "$file_path" =~ test.*\.py$ ]] || \
       [[ "$(basename "$file_path")" == "conftest.py" ]]; then
        return 0
    fi

    return 1
}

# Check if a file is an example/demo file
# Returns: 0 (true) if example file, 1 (false) otherwise
is_example_file() {
    local file_path="$1"

    # Check path components
    if [[ "$file_path" =~ (^|/)(examples?|demos?|samples?|tutorials?)/ ]]; then
        return 0
    fi

    # Check filename patterns
    if [[ "$file_path" =~ (example|demo|sample|tutorial).*\.py$ ]] || \
       [[ "$file_path" =~ .*_(example|demo|sample)\.py$ ]]; then
        return 0
    fi

    return 1
}

# Check if a file is documentation
# Returns: 0 (true) if doc file, 1 (false) otherwise
is_doc_file() {
    local file_path="$1"

    # Check path components
    if [[ "$file_path" =~ (^|/)(docs?|documentation|sphinx|_build)/ ]]; then
        return 0
    fi

    # Check if it's a markdown/rst/txt file (likely documentation)
    if [[ "$file_path" =~ \.(md|rst|txt|asciidoc|adoc)$ ]]; then
        return 0
    fi

    return 1
}

# Check if a file is in a virtual environment
# Returns: 0 (true) if in venv, 1 (false) otherwise
is_in_venv() {
    local file_path="$1"

    if [[ "$file_path" =~ (^|/)(venv|\.venv|env|virtualenv|\.virtualenv)/ ]]; then
        return 0
    fi

    return 1
}

# Check if a file is in __pycache__ or is a .pyc file
# Returns: 0 (true) if cache file, 1 (false) otherwise
is_cache_file() {
    local file_path="$1"

    if [[ "$file_path" =~ __pycache__/ ]] || \
       [[ "$file_path" =~ \.pyc$ ]] || \
       [[ "$file_path" =~ \.pyo$ ]]; then
        return 0
    fi

    return 1
}

# Check if a file is a build artifact
# Returns: 0 (true) if build artifact, 1 (false) otherwise
is_build_artifact() {
    local file_path="$1"

    if [[ "$file_path" =~ (^|/)(build|dist|\.eggs?|.*\.egg-info)/ ]]; then
        return 0
    fi

    return 1
}

# Check if a dependency manifest is for development/testing
# Returns: 0 (true) if dev dependency, 1 (false) otherwise
is_dev_dependency_file() {
    local file_path="$1"

    if [[ "$file_path" =~ requirements[_-]?dev\.txt$ ]] || \
       [[ "$file_path" =~ requirements[_-]?test\.txt$ ]] || \
       [[ "$file_path" =~ requirements[_-]?doc\.txt$ ]] || \
       [[ "$file_path" =~ dev[_-]?requirements\.txt$ ]] || \
       [[ "$file_path" =~ test[_-]?requirements\.txt$ ]]; then
        return 0
    fi

    return 1
}

# Calculate production likelihood score (0.0 to 1.0)
# Higher score = more likely to be production code
# Outputs: floating point number between 0.0 and 1.0
calculate_production_likelihood() {
    local file_path="$1"
    local score=1.0

    # Strong indicators of non-production code
    if is_in_venv "$file_path"; then
        score=0.0
    elif is_cache_file "$file_path"; then
        score=0.0
    elif is_build_artifact "$file_path"; then
        score=0.0
    elif is_doc_file "$file_path"; then
        score=0.1
    elif is_test_file "$file_path"; then
        score=0.2
    elif is_example_file "$file_path"; then
        score=0.3
    # Check for common production code indicators
    elif [[ "$file_path" =~ (^|/)(src|lib|app|core|api|models|views|controllers|services|utils)/ ]]; then
        score=1.0
    # Main package files
    elif [[ "$file_path" =~ __init__\.py$ ]] || \
         [[ "$file_path" =~ __main__\.py$ ]]; then
        score=0.9
    # Configuration files might have crypto settings
    elif [[ "$file_path" =~ (config|settings|constants).*\.py$ ]]; then
        score=0.8
    fi

    echo "$score"
}

# Get human-readable file type description
# Outputs: string describing the file type
get_file_type() {
    local file_path="$1"

    if is_in_venv "$file_path"; then
        echo "virtual_environment"
    elif is_cache_file "$file_path"; then
        echo "cache"
    elif is_build_artifact "$file_path"; then
        echo "build_artifact"
    elif is_test_file "$file_path"; then
        echo "test"
    elif is_example_file "$file_path"; then
        echo "example"
    elif is_doc_file "$file_path"; then
        echo "documentation"
    elif [[ "$file_path" =~ \.py$ ]]; then
        echo "source"
    elif [[ "$file_path" =~ requirements.*\.txt$ ]] || \
         [[ "$file_path" =~ Pipfile$ ]] || \
         [[ "$file_path" =~ setup\.py$ ]] || \
         [[ "$file_path" =~ pyproject\.toml$ ]]; then
        echo "dependency_manifest"
    else
        echo "unknown"
    fi
}

# Generate complete context metadata as JSON
# Args: file_path, [line_number]
# Outputs: JSON object with context metadata
generate_context_json() {
    local file_path="$1"
    local line_number="${2:-}"

    local file_type
    local is_test
    local is_example
    local is_doc
    local in_venv
    local is_dev_dep
    local likely_production
    local production_likelihood

    file_type=$(get_file_type "$file_path")
    is_test=$(is_test_file "$file_path" && echo "true" || echo "false")
    is_example=$(is_example_file "$file_path" && echo "true" || echo "false")
    is_doc=$(is_doc_file "$file_path" && echo "true" || echo "false")
    in_venv=$(is_in_venv "$file_path" && echo "true" || echo "false")
    is_dev_dep=$(is_dev_dependency_file "$file_path" && echo "true" || echo "false")
    production_likelihood=$(calculate_production_likelihood "$file_path")

    # Convert likelihood to boolean (threshold: 0.5)
    if (( $(echo "$production_likelihood >= 0.5" | bc -l 2>/dev/null || echo "0") )); then
        likely_production="true"
    else
        likely_production="false"
    fi

    # Build JSON (properly escaped)
    cat <<EOF
{
  "file_path": "$(echo "$file_path" | sed 's/"/\\"/g')",
  "file_type": "$file_type",
  "is_test_file": $is_test,
  "is_example_file": $is_example,
  "is_doc_file": $is_doc,
  "in_virtual_environment": $in_venv,
  "is_dev_dependency": $is_dev_dep,
  "production_likelihood": $production_likelihood,
  "likely_production": $likely_production$(if [ -n "$line_number" ]; then echo ","; echo "  \"line_number\": $line_number"; fi)
}
EOF
}

# Export functions for use in other scripts
export -f is_test_file
export -f is_example_file
export -f is_doc_file
export -f is_in_venv
export -f is_cache_file
export -f is_build_artifact
export -f is_dev_dependency_file
export -f calculate_production_likelihood
export -f get_file_type
export -f generate_context_json
