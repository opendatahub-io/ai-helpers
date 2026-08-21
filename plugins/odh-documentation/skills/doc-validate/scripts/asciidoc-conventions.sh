#!/usr/bin/env bash
# AsciiDoc modular framework conventions and helpers.
#
# Source this file to get helper functions:
#   source "${CLAUDE_SKILL_DIR}/scripts/asciidoc-conventions.sh"
#
# Self-contained: resolves product config via parse-product-config.py.

if [[ "${1:-}" == "--help" ]]; then
    echo "Usage: source asciidoc-conventions.sh"
    echo ""
    echo "AsciiDoc modular framework conventions and helper functions."
    echo "Source this file to use the following functions:"
    echo "  adoc_module_name <type> <slug>       - Generate module filename"
    echo "  adoc_module_id <type> <slug>         - Generate module ID (anchor)"
    echo "  adoc_module_type <filename>          - Detect module type from filename"
    echo "  adoc_concept_template <id> <title>   - Generate concept template"
    echo "  adoc_procedure_template <id> <title> - Generate procedure template"
    echo "  adoc_reference_template <id> <title> - Generate reference template"
    echo "  adoc_assembly_template <id> <title> <modules...> - Generate assembly"
    echo "  adoc_validate_structure <file>       - Check AsciiDoc structure"
    # shellcheck disable=SC2317
    return 0 2>/dev/null || exit 0
fi

_ADOC_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_ADOC_PROJECT_ROOT="$(git -C "$_ADOC_SCRIPTS_DIR" rev-parse --show-toplevel 2>/dev/null || pwd)"

# shellcheck disable=SC1091
source "${_ADOC_SCRIPTS_DIR}/load-env.sh"

_ADOC_CONFIG_PATH="${PRODUCT_CONFIG:-${_ADOC_PROJECT_ROOT}/configs/rhoai.yaml}"
_ADOC_PARSE_SCRIPT="${_ADOC_SCRIPTS_DIR}/parse-product-config.py"
_ADOC_PYTHON3="$(command -v python3 || command -v python)" || {
    echo "Error: python3 (or python) not found in PATH" >&2
    # shellcheck disable=SC2317
    return 1 2>/dev/null || exit 1
}

# _adoc_module_prefix <type>
# Return the module prefix for a given type via parse-product-config.py.
_adoc_module_prefix() {
    "$_ADOC_PYTHON3" "$_ADOC_PARSE_SCRIPT" "$_ADOC_CONFIG_PATH" --module-prefix "$1"
}

# adoc_module_name <type> <slug>
# Generate a module filename following naming conventions.
# Types: concept, procedure, reference, assembly, snippet
# Example: adoc_module_name concept "model-serving" -> "con_model-serving.adoc"
adoc_module_name() {
    local type="$1"
    local slug="$2"
    local prefix
    prefix=$(_adoc_module_prefix "$type")
    if [[ -z "$prefix" ]]; then
        echo "Error: unknown module type: $type" >&2
        return 1
    fi
    echo "${prefix}${slug}.adoc"
}

# adoc_module_id <type> <slug>
# Generate a module ID (anchor) following naming conventions.
# Example: adoc_module_id concept "model-serving" -> "con_model-serving"
adoc_module_id() {
    local type="$1"
    local slug="$2"
    local prefix
    prefix=$(_adoc_module_prefix "$type")
    if [[ -z "$prefix" ]]; then
        echo "Error: unknown module type: $type" >&2
        return 1
    fi
    echo "${prefix}${slug}"
}

# adoc_module_type <filename>
# Detect module type from filename prefix.
# Returns: concept, procedure, reference, assembly, snippet, or unknown
adoc_module_type() {
    local filename
    filename=$(basename "$1")

    case "$filename" in
        con_*)       echo "concept" ;;
        proc_*)      echo "procedure" ;;
        ref_*)       echo "reference" ;;
        assembly_*)  echo "assembly" ;;
        snip_*)      echo "snippet" ;;
        *)           echo "unknown" ;;
    esac
}

# adoc_concept_template <id> <title>
# Generate a concept module template.
adoc_concept_template() {
    local id="$1"
    local title="$2"
    cat <<EOF
// Module included in the following assemblies:
//
// <List assemblies here, each on a new line>

:_mod-docs-content-type: CONCEPT

[id="${id}_{context}"]
= ${title}

Write a short introductory paragraph that provides an overview of the concept.

EOF
}

# adoc_procedure_template <id> <title>
# Generate a procedure module template.
adoc_procedure_template() {
    local id="$1"
    local title="$2"
    cat <<EOF
// Module included in the following assemblies:
//
// <List assemblies here, each on a new line>

:_mod-docs-content-type: PROCEDURE

[id="${id}_{context}"]
= ${title}

This section describes how to...

.Prerequisites

* Prerequisite 1
* Prerequisite 2

.Procedure

. Step 1
. Step 2
. Step 3

.Verification

* Verification step 1

EOF
}

# adoc_reference_template <id> <title>
# Generate a reference module template.
adoc_reference_template() {
    local id="$1"
    local title="$2"
    cat <<EOF
// Module included in the following assemblies:
//
// <List assemblies here, each on a new line>

:_mod-docs-content-type: REFERENCE

[id="${id}_{context}"]
= ${title}

EOF
}

# adoc_assembly_template <id> <title> <modules...>
# Generate an assembly template including specified modules.
adoc_assembly_template() {
    local id="$1"
    local title="$2"
    shift 2
    local modules=("$@")

    cat <<EOF
:_mod-docs-content-type: ASSEMBLY

[id="${id}_{context}"]
= ${title}

:context: ${id}

EOF
    for mod in "${modules[@]}"; do
        local safe_mod="${mod##*/}"
        if [[ ! "$safe_mod" =~ ^[A-Za-z0-9._-]+(\.adoc)?$ ]]; then
            echo "Error: invalid module filename: $mod" >&2
            return 1
        fi
        [[ "$safe_mod" == *.adoc ]] || safe_mod="${safe_mod}.adoc"
        echo "include::modules/${safe_mod}[leveloffset=+1]"
        echo ""
    done
}

# adoc_validate_structure <file>
# Check basic AsciiDoc structure requirements.
# Returns 0 if valid, 1 if issues found. Issues printed to stderr.
adoc_validate_structure() {
    local file="$1"
    local issues=0

    if [[ ! -f "$file" ]]; then
        echo "Error: file not found: $file" >&2
        return 1
    fi

    # Check for module ID
    if ! grep -q '^\[id="' "$file"; then
        echo "Warning: no module ID found in $file" >&2
        issues=$((issues + 1))
    fi

    # Check for content type
    if ! grep -q ':_mod-docs-content-type:' "$file"; then
        echo "Warning: no content type attribute in $file" >&2
        issues=$((issues + 1))
    fi

    # Check for heading
    if ! grep -q '^= ' "$file"; then
        echo "Warning: no level-1 heading found in $file" >&2
        issues=$((issues + 1))
    fi

    return $issues
}
