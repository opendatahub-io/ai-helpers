#!/bin/bash
set -euo pipefail

STORAGE_ROOT=""
NO_HEADER=false
LOCAL_SCAN=false

: "${REDHAT_KEY:=199e2f91fd431d51}"
: "${ARCHS:=amd64}"
: "${DEFAULT_TAGS:=latest}"
: "${SIZE_WARN_MB:=1024}"
: "${AUTO_CONFIRM:=false}"

usage() {
    cat >&2 <<EOF
Usage: $0 [-s <storage_path>] [-H] [-y] <image_url> [tag1 tag2 ...]
       $0 [-s <storage_path>] [-H] [-y] -f <input_file> [tag1 tag2 ...]
       $0 [-H] -l

Extract non-Red Hat-signed RPMs from container images or the local machine.
Images larger than ${SIZE_WARN_MB}MB trigger a size warning before pulling.

Options:
  -h         Show this help message
  -l         Scan the local machine instead of a container image
  -s <path>  Podman storage root (passed as --root to podman)
  -H         Suppress CSV header (useful when appending to existing output)
  -y         Auto-confirm large image pulls (skip size warning prompt)

Arguments:
  image_url   Container image URL without tag (e.g. quay.io/rhoai/odh-vllm-rocm-rhel9)
  -f <file>   Read image URLs from file (one per line, # for comments)
  tag1 ...    Release tags to check (appended to image URL as :tag)

Environment variables:
  REDHAT_KEY    GPG key ID to identify Red Hat-signed packages
              (default: 199e2f91fd431d51)
  DEFAULT_TAGS    Space-separated release tags when none given on command line
                (default: latest)
  ARCHS           Space-separated architectures to pull
                (default: amd64)
  SIZE_WARN_MB    Warn before pulling images larger than this (in MB)
                (default: 1024)
  AUTO_CONFIRM    Set to 'true' to skip size warning prompts
                (default: false)

Image resolution:
  If the repository is not found, the script also tries appending -rhel9
  to the image name (e.g. odh-dashboard -> odh-dashboard-rhel9).

Tag resolution (when no tags are given on the command line):
  1. Try DEFAULT_TAGS (latest)
  2. Auto-discover tags via skopeo: pick the highest stable rhoai-X.Y tag,
     or the latest early access (EA) rhoai-* tag, or odh-pr-linux-x86-64

Prerequisites:
  Container mode: podman, skopeo, jq
  Local mode (-l): rpm

Examples:
  # Scan the local machine:
  $0 -l

  # Quick scan (amd64, auto-discovers tag if latest unavailable):
  $0 quay.io/rhoai/odh-vllm-rocm-rhel9

  # Scan specific release tags:
  $0 quay.io/rhoai/odh-vllm-rocm-rhel9 rhoai-3.4 rhoai-3.5

  # Skip size warning prompts for large images:
  $0 -y quay.io/rhoai/odh-training-cuda128-torch29-py312-rhel9

  # Scan all supported architectures:
  ARCHS="amd64 arm64 s390x ppc64le" $0 quay.io/rhoai/odh-vllm-rocm-rhel9

  # Full matrix — all architectures and multiple tags:
  ARCHS="amd64 arm64 s390x ppc64le" $0 quay.io/rhoai/odh-vllm-rocm-rhel9 rhoai-3.4 rhoai-3.5
EOF
    exit "${1:-1}"
}

while getopts ":hls:Hy" opt; do
    case $opt in
        h) usage 0 ;;
        l) LOCAL_SCAN=true ;;
        s) STORAGE_ROOT="$OPTARG" ;;
        H) NO_HEADER=true ;;
        y) AUTO_CONFIRM=true ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

host_arch() {
    local machine
    machine=$(uname -m)
    case "$machine" in
        x86_64)  echo "amd64" ;;
        aarch64) echo "arm64" ;;
        *)       echo "$machine" ;;
    esac
}

scan_local() {
    local hostname arch os_release
    hostname=$(hostname -s)
    arch=$(host_arch)
    os_release="local"
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        os_release=$(. /etc/os-release && echo "${ID:-linux}-${VERSION_ID:-unknown}")
    fi

    echo "[local] Scanning host: ${hostname} (${arch}, ${os_release})" >&2
    echo "[local] Extracting RPM info ..." >&2

    local raw_output
    raw_output=$(rpm -qai \
        | awk '/^Name/{name=$3} /^Signature/{if($0~/Key ID/){kid=$NF}else{kid="(none)"}; print name" "kid}')

    local total_pkgs
    total_pkgs=$(echo "$raw_output" | wc -l)
    local filtered_output
    filtered_output=$(echo "$raw_output" | grep -vi "${REDHAT_KEY}" || true)
    if [ -z "$filtered_output" ]; then
        echo "[local] All ${total_pkgs} packages are Red Hat-signed." >&2
        return 0
    fi
    local filtered_pkgs
    filtered_pkgs=$(echo "$filtered_output" | wc -l)
    echo "[local] Found ${filtered_pkgs} non-Red Hat packages (out of ${total_pkgs} total)." >&2

    while IFS=' ' read -r pkg_name key_id; do
        echo "local,${arch},${hostname},${os_release},${pkg_name},${key_id}"
    done <<< "$filtered_output"
}

if [ "$LOCAL_SCAN" = true ]; then
    if ! command -v rpm >/dev/null 2>&1; then
        echo "Error: rpm is not installed or not in PATH." >&2
        exit 1
    fi
    if [ "$NO_HEADER" = false ]; then
        echo "tag,arch,image_name,image_ref,pkg_name,key_id"
    fi
    scan_local
    exit 0
fi

for cmd in podman skopeo jq; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: ${cmd} is not installed or not in PATH." >&2
        exit 1
    fi
done

if [ $# -lt 1 ]; then
    usage
fi

PODMAN_OPTS=()
if [ -n "$STORAGE_ROOT" ]; then
    PODMAN_OPTS+=(--root "$STORAGE_ROOT")
    echo ">>> Using podman storage: ${STORAGE_ROOT}" >&2
fi

podman() { command podman "${PODMAN_OPTS[@]}" "$@"; }

read -ra ARCH_ARRAY <<< "$ARCHS"
read -ra DEFAULT_TAG_ARRAY <<< "$DEFAULT_TAGS"

IMAGES=()
if [ "$1" = "-f" ]; then
    if [ $# -lt 2 ]; then
        echo "Error: -f requires a file argument." >&2
        usage
    fi
    input_file="$2"
    if [ ! -f "$input_file" ]; then
        echo "Error: input file not found: ${input_file}" >&2
        exit 1
    fi
    if [ ! -r "$input_file" ]; then
        echo "Error: input file not readable: ${input_file}" >&2
        exit 1
    fi
    shift 2
    while IFS= read -r line; do
        [[ -z "$line" || "$line" == \#* ]] && continue
        IMAGES+=("$line")
    done < "$input_file"
else
    IMAGES+=("$1")
    shift
fi

if [ ${#IMAGES[@]} -eq 0 ]; then
    echo "Error: no images to process (file may be empty or all lines commented)." >&2
    exit 1
fi

USER_TAGS=false
if [ $# -gt 0 ]; then
    TAGS=("$@")
    USER_TAGS=true
else
    TAGS=("${DEFAULT_TAG_ARRAY[@]}")
fi

repo_exists() {
    local image="$1"
    local err
    err=$(skopeo inspect --raw "docker://${image}:latest" 2>&1 1>/dev/null) || true
    if echo "$err" | grep -q "repository not found"; then
        return 1
    fi
    return 0
}

resolve_image() {
    local image="$1"
    local image_name="${image##*/}"
    if repo_exists "$image"; then
        echo "$image"
        return 0
    fi
    if [[ "$image" != *-rhel9 ]]; then
        local alt="${image}-rhel9"
        echo "[${image_name}] Repository not found, trying ${alt##*/} ..." >&2
        if repo_exists "$alt"; then
            echo "[${image_name}] Resolved to ${alt##*/}" >&2
            echo "$alt"
            return 0
        fi
    fi
    echo "[${image_name}] Repository not found." >&2
    echo "$image"
}

discover_tags() {
    local image="$1"
    local image_name="${image##*/}"
    echo "[${image_name}] Discovering tags via skopeo ..." >&2
    local all_repo_tags
    all_repo_tags=$(skopeo list-tags "docker://${image}" 2>/dev/null \
        | jq -r '.Tags[]') || true
    if [ -z "$all_repo_tags" ]; then
        echo "[${image_name}] Could not list tags (repository not found?)." >&2
        return 1
    fi

    local release_tags
    release_tags=$(echo "$all_repo_tags" \
        | grep -E '^rhoai-[0-9]+\.[0-9]+(-[a-z]+\.[0-9]+)?$' \
        | sort -V || true)
    if [ -n "$release_tags" ]; then
        local count
        count=$(echo "$release_tags" | wc -l)
        echo "[${image_name}] Found ${count} rhoai-* release tag(s)." >&2

        local highest_version
        highest_version=$(echo "$release_tags" \
            | grep -oE '^rhoai-[0-9]+\.[0-9]+' \
            | sort -V \
            | tail -1) || true

        if [ -n "$highest_version" ]; then
            if echo "$release_tags" | grep -qx "$highest_version"; then
                echo "[${image_name}] Using latest stable tag: ${highest_version}" >&2
                echo "$highest_version"
                return 0
            fi

            local ea_tag
            ea_tag=$(echo "$release_tags" \
                | grep -E "^${highest_version}-" \
                | sort -V \
                | tail -1 || true)
            if [ -n "$ea_tag" ]; then
                echo "[${image_name}] No stable ${highest_version}, using early access: ${ea_tag}" >&2
                echo "$ea_tag"
                return 0
            fi
        fi

        local latest_tag
        latest_tag=$(echo "$release_tags" | tail -1)
        echo "[${image_name}] Using latest available: ${latest_tag}" >&2
        echo "$latest_tag"
        return 0
    fi

    if echo "$all_repo_tags" | grep -qx 'odh-pr-linux-x86-64'; then
        echo "[${image_name}] No rhoai-* tags found, using odh-pr-linux-x86-64." >&2
        echo "odh-pr-linux-x86-64"
        return 0
    fi

    echo "[${image_name}] No suitable tags found." >&2
    return 1
}

check_image_size() {
    local image="$1" tag="$2" arch="$3"
    local image_name="${image##*/}"
    local container_image="${image}:${tag}"
    local size_bytes
    size_bytes=$(skopeo inspect --override-arch "$arch" "docker://${container_image}" 2>/dev/null \
        | jq '[.LayersData[].Size] | add // 0') || true
    if [ -z "$size_bytes" ] || [ "$size_bytes" = "0" ] || [ "$size_bytes" = "null" ]; then
        echo "[${image_name}/${tag}/${arch}] Image size: unknown" >&2
        return 0
    fi
    local size_mb=$((size_bytes / 1024 / 1024))
    if [ "$size_mb" -ge "$SIZE_WARN_MB" ]; then
        echo "WARNING: ${container_image} (${arch}) is ~${size_mb}MB (compressed)." >&2
        if [ "$AUTO_CONFIRM" = true ]; then
            echo "  Auto-confirmed (-y flag), proceeding." >&2
            return 0
        fi
        if [ -t 0 ]; then
            read -r -p "  Continue pulling? [y/N] " answer </dev/tty
            case "$answer" in
                [yY]*) return 0 ;;
                *) echo "  Skipping." >&2; return 1 ;;
            esac
        else
            echo "  Non-interactive mode, proceeding anyway." >&2
        fi
    else
        echo "[${image_name}/${tag}/${arch}] Image size: ~${size_mb}MB (compressed)" >&2
    fi
    return 0
}

scan_tag() {
    local image="$1" tag="$2"
    local image_name="${image##*/}"
    local container_image="${image}:${tag}"
    local pull_failed=0

    for arch in "${ARCH_ARRAY[@]}"; do
        if ! check_image_size "$image" "$tag" "$arch"; then
            pull_failed=$((pull_failed + 1))
            continue
        fi
        echo "[${image_name}/${tag}/${arch}] Pulling ..." >&2
        if ! podman pull --platform "linux/${arch}" "${container_image}" >&2 2>&1; then
            echo "[${image_name}/${tag}/${arch}] Not available, skipping." >&2
            pull_failed=$((pull_failed + 1))
            continue
        fi

        image_digest=$(podman inspect --format '{{.Digest}}' "${container_image}")
        local image_ref="${image}@${image_digest}"
        echo "[${image_name}/${tag}/${arch}] Digest: ${image_digest}" >&2

        echo "[${image_name}/${tag}/${arch}] Extracting RPM info ..." >&2
        raw_output=$(podman run --rm --platform "linux/${arch}" --entrypoint /bin/bash "${container_image}" -c 'rpm -qai | awk "/^Name/{name=\$3} /^Signature/{if(\$0~/Key ID/){kid=\$NF}else{kid=\"(none)\"}; print name\" \"kid}"')

        total_pkgs=$(echo "$raw_output" | wc -l)
        filtered_output=$(echo "$raw_output" | grep -vi "${REDHAT_KEY}" || true)
        if [ -z "$filtered_output" ]; then
            echo "[${image_name}/${tag}/${arch}] All ${total_pkgs} packages are Red Hat-signed." >&2
            continue
        fi
        filtered_pkgs=$(echo "$filtered_output" | wc -l)
        echo "[${image_name}/${tag}/${arch}] Found ${filtered_pkgs} non-Red Hat packages (out of ${total_pkgs} total)." >&2

        while IFS=' ' read -r pkg_name key_id; do
            echo "${tag},${arch},${image_name},${image_ref},${pkg_name},${key_id}"
        done <<< "$filtered_output"
    done

    echo "[${image_name}/${tag}] Cleaning up ..." >&2
    podman rm -f "$(podman ps -a -q --filter "ancestor=${container_image}")" 2>/dev/null || true
    podman rmi -f "${container_image}" >/dev/null 2>&1 || true

    return "$pull_failed"
}

if [ "$NO_HEADER" = false ]; then
    echo "tag,arch,image_name,image_ref,pkg_name,key_id"
fi

for RAW_IMAGE in "${IMAGES[@]}"; do
    IMAGE=$(resolve_image "$RAW_IMAGE")
    image_name="${IMAGE##*/}"
    all_tags_failed=true

    for tag in "${TAGS[@]}"; do
        pull_failures=0
        scan_tag "$IMAGE" "$tag" || pull_failures=$?
        if [ "$pull_failures" -lt "${#ARCH_ARRAY[@]}" ]; then
            all_tags_failed=false
        fi
    done

    if [ "$all_tags_failed" = true ] && [ "$USER_TAGS" = false ]; then
        echo "[${image_name}] Default tag(s) not available, auto-discovering tags ..." >&2
        discovered_tag=$(discover_tags "$IMAGE") || true
        if [ -n "$discovered_tag" ]; then
            scan_tag "$IMAGE" "$discovered_tag" || true
        fi
    fi
done

ALL_ARCHS="amd64 arm64 s390x ppc64le"
scanned="${ARCHS}"
not_scanned=""
for a in $ALL_ARCHS; do
    found=false
    for s in ${scanned}; do
        if [ "$a" = "$s" ]; then found=true; break; fi
    done
    if [ "$found" = false ]; then
        not_scanned="${not_scanned:+${not_scanned} }${a}"
    fi
done

echo "" >&2
echo "=== Scan complete ===" >&2
echo "Architectures scanned: ${scanned}" >&2
if [ -n "$not_scanned" ]; then
    echo "WARNING: architectures NOT scanned: ${not_scanned}" >&2
    echo "  Other architectures of the same image:tag may contain different packages." >&2
    echo "  To scan all architectures, re-run with: ARCHS=\"${ALL_ARCHS}\"" >&2
fi
