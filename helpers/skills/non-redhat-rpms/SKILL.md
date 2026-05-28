---
name: non-redhat-rpms
description: >
  Use this skill to identify non-Red Hat RPM packages installed in container
  images or on the local machine. For containers, pulls images across multiple
  architectures and release tags; for local scans, inspects the host directly.
  Extracts RPM signing metadata and reports packages not signed with the Red Hat
  GPG key as CSV output. Use when auditing compliance, checking supply-chain
  provenance, or scanning for third-party RPMs in RHOAI component images.
allowed-tools: Bash
user-invocable: true
argument-hint: "<image_url_or_-f_input_file> [tag1 tag2 ...] | -l"
metadata:
  author: ODH
  version: "1.0"
  tags: compliance, rpms, container-images, audit
---

# Non-Red Hat RPMs

Identify non-Red Hat-signed RPM packages in container images or on the local
machine for compliance and supply-chain auditing.

## Agent Instructions

### Local vs container scan

If the user asks to scan "this machine", "the host", "localhost", or similar,
run the script with `-l`. No image URL, tags, or network access are needed:

```bash
./scripts/find_non_redhat_rpms.sh -l
```

For container image scans, follow the sections below.

### Image URL defaults

When the user requests a scan of an image without specifying the full URL:

- **Default registry**: `quay.io`
- **Default repositories** (in priority order): `rhoai`, then `opendatahub`
- Try `quay.io/rhoai/<image>` first. If the image is not found there, try
  `quay.io/opendatahub/<image>`.
- If the user provides a registry (e.g. `registry.redhat.io`) or repository
  (e.g. `opendatahub`), use those instead of the defaults.

The script automatically resolves component names: if a repository is not
found, it tries appending `-rhel9` (e.g. `odh-dashboard` resolves to
`odh-dashboard-rhel9`). Pass the user's input as-is and let the script
handle the resolution.

For example, if the user says "scan odh-dashboard", run the script against
`quay.io/rhoai/odh-dashboard`. The script will find that the repo doesn't
exist and automatically try `quay.io/rhoai/odh-dashboard-rhel9`.
If `quay.io/rhoai/` fails entirely, try `quay.io/opendatahub/` as the
repository.

### Large image confirmation

The script always displays the compressed image size before pulling. For
images exceeding 1 GB it prints a `WARNING:` line to stderr.

When the tag is known before running the script, pre-check the size to
decide whether to ask the user first:

```bash
skopeo inspect --override-arch amd64 "docker://<image>:<tag>" | jq '[.LayersData[].Size] | add'
```

If the total exceeds 1 GB (1073741824 bytes), **stop and ask the user for
confirmation in the chat** before proceeding. Only run the script with `-y`
after the user confirms. Do not repeat the size in your response — the
script already displays it in its output.

### Tag selection

When the user does not specify a tag, discover available tags before running
the script so you can offer a choice:

```bash
skopeo list-tags "docker://<image>" | jq -r '.Tags[]' \
  | grep -E '^rhoai-[0-9]+\.[0-9]+(-[a-z]+\.[0-9]+)?$' | sort -V
```

If there are multiple release tags (stable and/or early access), present
them to the user and let them pick which tag to scan. Show the highest
stable tag and the highest EA tag as the recommended options, for example:

> Available tags for odh-dashboard-rhel9:
> - rhoai-3.4 (stable)
> - rhoai-3.5-ea.2 (early access)
>
> Which tag would you like to scan?

If the user does not have a preference, default to the highest version —
preferring a stable tag over an early access tag at the same version.
Then run the script with the chosen tag as a positional argument.

### Multi-image scans

When scanning multiple images, batch tag-discovery and size-check commands
into a **single shell call** using a loop (with `&` / `wait` for
parallelism). This avoids prompting the user to approve a separate custom
command for every image:

```bash
for img in img-a img-b img-c; do
  (skopeo list-tags "docker://quay.io/rhoai/${img}" 2>/dev/null \
    | jq -r '.Tags[]' \
    | grep -E '^rhoai-[0-9]+\.[0-9]+(-[a-z]+\.[0-9]+)?$' | sort -V \
    | awk -v name="$img" '{print name": "$0}') &
done
wait
```

The same approach applies to size pre-checks — one shell call, one
approval.

### Results presentation

Always present scan results as a **markdown table**, never as plain-text
sentences. Include every scanned image as a row, even when the result is
"clean". Example:

```markdown
| Image | Tag | Arch | Non-RH pkgs | Details |
|-------|-----|------|-------------|---------|
| odh-dashboard-rhel9 | rhoai-3.4 | amd64 | 0 | Clean |
| odh-vllm-rhel9 | rhoai-3.5-ea.2 | amd64 | 3 | pkg-a, pkg-b, pkg-c |
```

## How It Works

The script supports two modes:

- **Container mode** (default): Pulls each image for every combination of
  release tag and CPU architecture, runs `rpm -qai` inside the container to
  extract package signing info, then filters out packages signed with the Red
  Hat GPG key.
- **Local mode** (`-l`): Runs `rpm -qai` directly on the host machine. No
  container runtime or network access is required.

In both modes the remaining non-Red Hat packages are emitted as CSV rows to
stdout. Progress and diagnostics are printed to stderr, so the CSV output can
be redirected or piped cleanly.

## Usage

Run the script from this skill's directory:

```bash
./scripts/find_non_redhat_rpms.sh -h
```

Scan the local machine:

```bash
./scripts/find_non_redhat_rpms.sh -l > results.csv
```

Quick scan of a single image (amd64, latest tag):

```bash
./scripts/find_non_redhat_rpms.sh quay.io/rhoai/odh-vllm-rocm-rhel9 > results.csv
```

Scan specific release tags:

```bash
./scripts/find_non_redhat_rpms.sh quay.io/rhoai/odh-vllm-rocm-rhel9 rhoai-3.4 rhoai-3.5-ea.1 > results.csv
```

Scan all supported architectures:

```bash
ARCHS="amd64 arm64 s390x ppc64le" ./scripts/find_non_redhat_rpms.sh quay.io/rhoai/odh-vllm-rocm-rhel9 > results.csv
```

Full matrix -- all architectures and multiple tags:

```bash
ARCHS="amd64 arm64 s390x ppc64le" ./scripts/find_non_redhat_rpms.sh quay.io/rhoai/odh-vllm-rocm-rhel9 rhoai-3.4 rhoai-3.5-ea.1 > results.csv
```

Multiple images from a file with custom tags:

```bash
./scripts/find_non_redhat_rpms.sh -f images.input rhoai-3.4 rhoai-3.5-ea.1 > results.csv
```

Append to an existing CSV (suppress header with `-H`):

```bash
./scripts/find_non_redhat_rpms.sh -H quay.io/rhoai/odh-vllm-gaudi-rhel9 >> results.csv
```

Run `-h` to see all options, environment variable overrides, and defaults.

## Input File Format

One image URL per line (without tag). Lines starting with `#` and blank lines
are ignored.

## Output Format

CSV with header row:

```text
tag,arch,image_name,image_ref,pkg_name,key_id
```

| Column | Description |
|--------|-------------|
| tag | Release tag used (e.g. `rhoai-3.4`) |
| arch | CPU architecture (e.g. `amd64`) |
| image_name | Short image name (last path segment) |
| image_ref | Full image reference with digest |
| pkg_name | RPM package name |
| key_id | GPG key ID that signed the package, or `(none)` |

## Gotchas

- On Fedora hosts, **all** packages will be flagged because the default
  `REDHAT_KEY` matches the RHEL GPG key, not the Fedora signing key. This is
  expected. Set `REDHAT_KEY` to the Fedora key if scanning a Fedora machine
  for non-Fedora packages.
- `gpg-pubkey` entries with key ID `(none)` are RPM-internal placeholders,
  not real third-party software. They appear in virtually every image.
- The `-l` flag ignores `ARCHS`, tags, and all container-related options.
  Do not combine `-l` with image URLs.
- Large images (>1 GB) prompt for confirmation in interactive mode. When
  running from an AI agent, always pass `-y` to avoid hanging on a TTY
  prompt.

## Prerequisites

- **Local mode** (`-l`): `rpm`
- **Container mode**: `podman`, `skopeo`, `jq`, network access to the
  container registry, and sufficient disk space for pulling images (cleaned
  up after each tag)
