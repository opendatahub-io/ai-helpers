#!/usr/bin/env python3
"""
Classify and filter bugfix PRs for backport relevance.

Reads raw-prs.json (from fetch-bugfix-prs.sh), checks file existence at a
target git tag, detects subsystems, and outputs filtered.json with
classification and file-level analysis.

PRs classified as "unclear" are NOT auto-decided — the agent reviews them.

Usage:
  python3 scripts/classify-and-filter.py \
    --input artifacts/backport-triage/raw-prs.json \
    --repo /path/to/vllm \
    --tag v0.13.0 \
    --output artifacts/backport-triage/filtered.json
"""

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

NON_RUNTIME_PATTERNS = [
    r"^tests/", r"^\.github/", r"^\.buildkite/", r"^docs/",
    r"^Dockerfile", r"^docker/", r"^\.pre-commit",
    r"^CONTRIBUTING", r"^README", r"^LICENSE",
    r"\.md$", r"^Makefile$", r"^\.gitignore$",
]

BUGFIX_TITLE_PATTERNS = [
    r"\[Bug\s*[Ff]ix\]", r"\[Bug\]", r"\[Fix\]",
    r"\[Bigfix\]",  # intentional: matches common misspelling in vLLM PR titles
]

NOT_BUGFIX_TITLE_PATTERNS = [
    r"^\[Feature\]", r"^\[Feat\]", r"^\[Perf\]", r"^\[RFC\]",
    r"^\[Refactor\]", r"^\[Misc\]", r"^\[Model\]", r"^\[Kernel",
    r"^\[Core\]", r"^\[Frontend\]", r"^\[Distributed\]",
    r"^\[CI\]", r"^\[Build\]", r"^\[Docs?\]", r"^\[Mypy\]",
    r"^\[CI/Build\]", r"^\[CI\]\[Build\]", r"^\[CI\]\[Bugfix\]",
    r"^\[Docker\]", r"^\[Release\]", r"^\[Test\]",
]

PLATFORM_SKIP_TAGS = ["rocm", "tpu", "cpu", "intel-gpu", "xpu"]
PLATFORM_TITLE_PATTERNS = [
    r"\[ROCm\]", r"\[TPU\]", r"\[CPU\]", r"\[XPU\]", r"\[Intel[- ]?GPU\]",
    r"\bROCm\b", r"\bTPU\b", r"\bXPU\b",
]

SUBSYSTEM_RULES = [
    ("attention",     [r"vllm/.*/attention/"]),
    ("scheduler",     [r"vllm/v1/core/", r"vllm/core/"]),
    ("engine",        [r"vllm/v1/engine/", r"vllm/engine/"]),
    ("api/frontend",  [r"vllm/entrypoints/"]),
    ("models",        [r"vllm/model_executor/models/"]),
    ("quantization",  [r"vllm/model_executor/layers/quantization/"]),
    ("sampling",      [r"vllm/v1/sample/", r"vllm/model_executor/layers/sampler"]),
    ("distributed",   [r"vllm/distributed/"]),
    ("lora",          [r"vllm/lora/"]),
    ("spec_decode",   [r"vllm/spec_decode/", r"vllm/v1/spec_decode/"]),
    ("multimodal",    [r"vllm/multimodal/"]),
    ("config",        [r"vllm/config"]),
    ("worker",        [r"vllm/v1/worker/", r"vllm/worker/"]),
    ("kernels",       [r"vllm/model_executor/layers/", r"csrc/"]),
]

REPO = "vllm-project/vllm"


def run(cmd, check=True, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, check=check,
                       timeout=120, cwd=cwd)
    return r.stdout.strip()


def file_exists_at_tag(repo_path, tag, filepath):
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{tag}:{filepath}"],
            capture_output=True, check=True, timeout=10, cwd=repo_path,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def classify_pr(title, labels):
    label_names = {l.lower() for l in labels}
    if label_names & set(PLATFORM_SKIP_TAGS):
        return "platform_specific"
    if any(re.search(p, title, re.IGNORECASE) for p in PLATFORM_TITLE_PATTERNS):
        return "platform_specific"
    if any(re.search(p, title, re.IGNORECASE) for p in NOT_BUGFIX_TITLE_PATTERNS):
        return "not_bugfix"
    if "bug" in label_names:
        return "runtime_bug"
    if any(re.search(p, title) for p in BUGFIX_TITLE_PATTERNS):
        return "runtime_bug"
    if re.search(r"\bfix\b", title, re.IGNORECASE):
        return "unclear"
    return "not_bugfix"


def is_non_runtime(filepath):
    return any(re.search(p, filepath) for p in NON_RUNTIME_PATTERNS)


def detect_subsystems(files):
    found = set()
    for f in files:
        for name, patterns in SUBSYSTEM_RULES:
            if any(re.search(p, f) for p in patterns):
                found.add(name)
    return sorted(found)


def fetch_files(pr_number):
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", REPO,
         "--json", "files", "--jq", ".files[].path"],
        capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  Warning: gh pr view #{pr_number} failed: {result.stderr.strip()}",
              file=sys.stderr)
        return []
    raw = result.stdout.strip()
    return raw.split("\n") if raw else []


def process_pr(pr, repo_path, tag):
    num = pr["number"]
    title = pr["title"]
    labels = pr.get("label_names", [])
    classification = classify_pr(title, labels)

    if classification in ("not_bugfix", "platform_specific"):
        return {
            **pr,
            "classification": classification,
            "skip_reason": "not a bugfix (Feature/Perf/CI/Refactor)"
                           if classification == "not_bugfix"
                           else "platform-specific (ROCm/TPU/XPU)",
            "verdict": "SKIP",
        }

    files = fetch_files(num)
    existing = []
    new_files = []
    for f in files:
        if file_exists_at_tag(repo_path, tag, f):
            existing.append(f)
        else:
            new_files.append(f)
    runtime_existing = [f for f in existing if not is_non_runtime(f)]
    subsystems = detect_subsystems(files)

    if not files:
        verdict, skip_reason = "SKIP", "no files detected"
    elif not existing:
        verdict, skip_reason = "SKIP", "all files are post-release"
    elif not runtime_existing:
        verdict, skip_reason = "SKIP", "only touches tests/docs/CI files"
    else:
        verdict, skip_reason = "CANDIDATE", ""

    return {
        **pr,
        "classification": classification,
        "verdict": verdict,
        "skip_reason": skip_reason,
        "files": files,
        "files_in_release": existing,
        "files_new": new_files,
        "files_in_release_count": len(existing),
        "files_total": len(files),
        "subsystems": subsystems,
    }


def main():
    parser = argparse.ArgumentParser(description="Classify and filter bugfix PRs")
    parser.add_argument("--input", required=True, help="Path to raw-prs.json")
    parser.add_argument("--repo", required=True, help="Path to vLLM git checkout")
    parser.add_argument("--tag", required=True, help="Target release tag (e.g. v0.13.0)")
    parser.add_argument("--output", required=True, help="Output path for filtered.json")
    args = parser.parse_args()

    try:
        subprocess.run(["git", "rev-parse", "--verify", args.tag],
                       capture_output=True, check=True, cwd=args.repo)
    except subprocess.CalledProcessError:
        print(f"Error: tag '{args.tag}' not found in {args.repo}", file=sys.stderr)
        sys.exit(1)

    with open(args.input) as f:
        prs = json.load(f)

    print(f"Loaded {len(prs)} PRs from {args.input}", file=sys.stderr)

    results = []
    counts = {"runtime_bug": 0, "not_bugfix": 0, "platform_specific": 0, "unclear": 0}

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(process_pr, pr, args.repo, args.tag): pr for pr in prs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            counts[result["classification"]] = counts.get(result["classification"], 0) + 1

    results.sort(key=lambda r: r.get("mergedAt", ""))

    candidates = [r for r in results if r["verdict"] == "CANDIDATE"]
    unclear = [r for r in results if r["classification"] == "unclear"]

    print(f"\nClassification:", file=sys.stderr)
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}", file=sys.stderr)
    print(f"\nCandidates: {len(candidates)}", file=sys.stderr)
    print(f"Unclear (needs agent review): {len(unclear)}", file=sys.stderr)

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Output: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
