#!/usr/bin/env bash
# AsciiDoc modular framework conventions and helpers.
#
# Source this file to get helper functions:
#   source "${CLAUDE_SKILL_DIR}/scripts/asciidoc-conventions.sh"
#
# Requires: source product-config.sh first (from same scripts/ directory)

# adoc_module_name <type> <slug>
# Generate a module filename following naming conventions.
# Types: concept, procedure, reference, assembly, snippet
# Example: adoc_module_name concept "model-serving" -> "con_model-serving.adoc"
adoc_module_name() {
    local type="$1"
    local slug="$2"
    local prefix
    prefix=$(pc_module_prefix "$type")
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
    prefix=$(pc_module_prefix "$type")
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
        echo "include::modules/${mod}[leveloffset=+1]"
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
