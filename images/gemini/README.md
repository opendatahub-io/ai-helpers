# gemini-ai-helpers Container Image

A UBI 10-based container image that pairs Google's Gemini CLI with the same rich
tooling layer used by the [Claude ai-helpers image](../claude/) — giving Gemini
agents a capable, Red Hat-compatible environment to operate in.

## Quick start

```bash
podman pull quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

Run an interactive session:

```bash
podman run -it --rm \
  --env GEMINI_API_KEY=your-key-here \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

## What's included

| Tool | Version | Install method | Purpose |
|------|---------|----------------|---------|
| gemini-cli | 0.53.0 | npm (system-wide) | Google Gemini AI agent |
| jq | latest (UBI) | dnf | JSON processing |
| yq | 4.53.3 | binary + SHA256 | YAML processing |
| ripgrep (`rg`) | 15.2.0 | binary + SHA256 | Fast code search |
| jc | latest | uv pip | Converts CLI output to JSON |
| shellcheck | 0.11.0 | binary + SHA256 | Shell script linting |
| gh | 2.89.0 | binary + SHA256 | GitHub CLI |
| glab | 1.91.0 | binary + SHA256 | GitLab CLI |
| oc | stable | binary | OpenShift client |
| gcloud | latest | dnf (yum repo) | Google Cloud CLI |
| uv | latest | installer | Python package manager |
| Python 3 | system | dnf | Scripting runtime |
| Python packages | — | uv pip | pytest, requests, pyyaml, ruff, tox, tox-uv, jc |
| Node.js | system | dnf | Runtime for gemini-cli |

All binaries are verified with pinned SHA256 checksums at build time.
Supports `x86_64` and `aarch64`.

The full [ai-helpers](https://github.com/opendatahub-io/ai-helpers) skill and agent
library is cloned to `/opt/ai-helpers` at image build time and available on disk for
all sessions.

## Authentication

Gemini CLI supports two authentication methods: API key and Google account OAuth.
Choose the method that matches your use case — the reasoning below is genuine.

### Option 1: Environment variable (`GEMINI_API_KEY`)

```bash
podman run -it --rm \
  --env GEMINI_API_KEY=AIzaSy... \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

To avoid putting the key in your shell history, read it from a file at run time:

```bash
podman run -it --rm \
  --env GEMINI_API_KEY="$(cat ~/.config/gemini/api-key)" \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

**Choose this method when:**
- Running in CI/CD pipelines (inject via a pipeline secret — Tekton, GitHub Actions,
  GitLab CI, Jenkins all handle this natively)
- Deploying to Kubernetes or OpenShift, where a `Secret` resource is the idiomatic
  way to deliver credentials to a container
- The container is ephemeral and short-lived — the key is injected per-run and never
  persists anywhere in the image or on the host
- You are scripting or automating non-interactive workloads and want a clean,
  stateless credential model

**Why not always use this?**
The key is visible in `podman inspect` on the running container and appears in the
container's `/proc/<pid>/environ`. On a shared host or in an environment with
broad container-inspect permissions, this is a meaningful exposure. It also cannot
carry OAuth tokens — only bare API keys.

---

### Option 2: Bind-mount `~/.gemini/`

If you have authenticated gemini-cli on your host (either with `gemini auth` for
Google account OAuth, or by configuring an API key through the CLI), your credentials
live in `~/.gemini/`. Bind-mounting that directory gives the container the same
authenticated identity without exposing anything in environment variables.

```bash
podman run -it --rm \
  --volume "${HOME}/.gemini:/home/gemini/.gemini:ro,Z" \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

> The `:Z` flag relabels the mount for SELinux on RHEL/Fedora. Use `:z` if the
> directory will be shared across multiple containers simultaneously.

**Choose this method when:**
- You use Google account OAuth (the `gemini auth` flow) rather than a bare API key —
  OAuth tokens cannot be injected as a simple env var
- You are doing interactive development on a workstation and want the container to
  feel like a native install — same credentials, no per-run ceremony
- You want to rotate or update credentials by editing a file on the host, with no
  container rebuild or restart required
- You are on a shared host where other users can run `podman inspect` — the mount
  path appears in inspect output, but the credential values do not

**Why not always use this?**
It creates a coupling between the host filesystem and the container. In CI/CD or
Kubernetes, there is no persistent home directory to mount from, so this method does
not apply. It also means the container is not fully stateless — behavior depends on
what is in the host directory at run time.

---

### Kubernetes / OpenShift

Use a `Secret` to deliver the API key as an environment variable:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gemini-api-key
type: Opaque
stringData:
  GEMINI_API_KEY: "AIzaSy..."
```

```yaml
env:
  - name: GEMINI_API_KEY
    valueFrom:
      secretKeyRef:
        name: gemini-api-key
        key: GEMINI_API_KEY
```

## Running examples

Pass a one-shot prompt:

```bash
podman run --rm \
  --env GEMINI_API_KEY="$(cat ~/.config/gemini/api-key)" \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest \
  -p "Summarise the key changes in the Linux 6.10 release notes"
```

Mount a local repository for analysis:

```bash
podman run -it --rm \
  --env GEMINI_API_KEY="$(cat ~/.config/gemini/api-key)" \
  --volume "$(pwd):/workspace:ro,Z" \
  --workdir /workspace \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

Use host credentials and a local repo together:

```bash
podman run -it --rm \
  --volume "${HOME}/.gemini:/home/gemini/.gemini:ro,Z" \
  --volume "$(pwd):/workspace:ro,Z" \
  --workdir /workspace \
  quay.io/YOUR_ORG/gemini-ai-helpers:latest
```

## Build information

The image is built and published from
[heatmiser/ee-builds](https://github.com/heatmiser/ee-builds) via GitHub Actions:

- **Pull requests** → `ghcr.io/heatmiser/gemini-ai-helpers:pr-<number>-<sha>`
- **Merge to main** → `quay.io/YOUR_ORG/gemini-ai-helpers:latest`

The base image is `registry.access.redhat.com/ubi10/ubi:10.2` (public, no Red Hat
subscription required).
