#!/usr/bin/env python3
"""Six-stage context filtering pipeline.

Accepts a JSON list of candidate files and task context, returns a filtered
and scored set. Ported from docagent's filtering pipeline.

Usage:
    python3 context-filter.py --candidates candidates.json --task-context task.json
    echo '{"candidates": [...], "task_context": {...}}' | python3 context-filter.py

Input JSON structure:
{
    "candidates": [
        {
            "source_type": "documentation",
            "repo": "opendatahub-io/opendatahub-documentation",
            "git_ref": "main",
            "file_path": "modules/serving/pages/con_model-serving.adoc",
            "content": "...",
            "size_bytes": 4521
        }
    ],
    "task_context": {
        "jira_key": "RHOAIENG-55490",
        "summary": "Add model serving documentation",
        "description": "...",
        "components": ["Model Serving", "kserve"],
        "keywords": ["model", "serving", "inference"],
        "product_version": "2.18"
    },
    "source_declarations": [
        {
            "source_type": "documentation",
            "always_include": true,
            "components": null,
            "path_hints": ["modules/**/*.adoc"]
        }
    ],
    "token_budget": 100000
}

Output JSON: filtered list of candidates with relevance scores and signals.
"""

import argparse
import fnmatch
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env file from project root (cwd) if it exists. Existing env vars take precedence."""
    env_path = Path.cwd() / ".env"
    if not env_path.is_file():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key not in os.environ:
                os.environ[key] = value


_load_dotenv()


# --- Models ---

STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
    }
)


def extract_keywords(text: str) -> list[str]:
    """Extract keywords from text by removing stop words and normalizing."""
    words = re.findall(r"\w+", text.lower())
    keywords = [w for w in words if w not in STOP_WORDS]
    seen = set()
    result = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words."""
    return re.findall(r"\w+", text.lower())


# --- BM25 Implementation ---


class BM25:
    """BM25Okapi scoring without external dependencies."""

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lengths) / self.corpus_size if self.corpus_size else 1.0

        # Build document frequency
        self.df: dict[str, int] = {}
        for doc in corpus:
            unique_terms = set(doc)
            for term in unique_terms:
                self.df[term] = self.df.get(term, 0) + 1

        # Precompute IDF
        self.idf: dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

        # Build term frequencies per document
        self.tf: list[dict[str, int]] = []
        for doc in corpus:
            tf = Counter(doc)
            self.tf.append(dict(tf))

    def get_scores(self, query: list[str]) -> list[float]:
        """Score all documents against the query."""
        scores = []
        for i in range(self.corpus_size):
            score = 0.0
            doc_len = self.doc_lengths[i]
            for term in query:
                if term not in self.tf[i]:
                    continue
                tf = self.tf[i][term]
                idf = self.idf.get(term, 0.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += idf * numerator / denominator
            scores.append(score)
        return scores


# --- Filter Stages ---


def stage_static_inclusion(candidates: list[dict], source_declarations: list[dict]) -> list[dict]:
    """Stage 1: Mark candidates from always_include sources as static."""
    decl_map = {d["source_type"]: d for d in source_declarations}
    result = []
    for c in candidates:
        c = dict(c)
        decl = decl_map.get(c.get("source_type", ""))
        if decl and decl.get("always_include", False):
            c["static"] = True
            c.setdefault("signals", []).append(
                {
                    "filter": "static_inclusion",
                    "passed": True,
                    "reason": "Source marked with always_include=True",
                }
            )
        else:
            c["static"] = c.get("static", False)
            c.setdefault("signals", []).append(
                {
                    "filter": "static_inclusion",
                    "passed": True,
                    "reason": "Optional source (not static)",
                }
            )
        result.append(c)
    return result


def stage_component_affinity(
    candidates: list[dict], task_context: dict, source_declarations: list[dict]
) -> list[dict]:
    """Stage 3: Filter candidates by component affinity."""
    decl_map = {d["source_type"]: d for d in source_declarations}
    task_components = set(c.lower() for c in task_context.get("components", []))
    result = []
    for c in candidates:
        c = dict(c)
        decl = decl_map.get(c.get("source_type", ""))
        if decl is None or decl.get("components") is None:
            c.setdefault("signals", []).append(
                {
                    "filter": "component_affinity",
                    "passed": True,
                    "reason": (
                        "No component affinity configured for"
                        f" source type '{c.get('source_type', '')}'"
                    ),
                }
            )
            result.append(c)
            continue

        source_components = set(comp.lower() for comp in decl["components"])
        matching = source_components & task_components
        if matching:
            c.setdefault("signals", []).append(
                {
                    "filter": "component_affinity",
                    "passed": True,
                    "reason": f"Component affinity matches: {', '.join(sorted(matching))}",
                }
            )
            result.append(c)
        # No match: candidate excluded
    return result


def stage_path_relevance(
    candidates: list[dict], task_context: dict, path_hints: list[str]
) -> list[dict]:
    """Stage 4: Score candidates by path relevance."""
    keywords = set(k.lower() for k in task_context.get("keywords", []))
    components = set(c.lower() for c in task_context.get("components", []))

    raw_scores = []
    for c in candidates:
        file_path = c.get("file_path", "")
        if not file_path:
            raw_scores.append(0.0)
            continue

        path_lower = file_path.lower()
        path_parts = set(Path(path_lower).parts)
        stem = Path(path_lower).stem

        # Component matches (weight 2.0)
        comp_matches = path_parts & components
        # Keyword matches (weight 1.0)
        kw_matches = path_parts & keywords
        for kw in keywords:
            if kw in stem and kw not in kw_matches:
                kw_matches.add(kw)
        # Hint matches (weight 1.0) — use fnmatch for glob pattern support
        hint_count = sum(1 for h in path_hints if fnmatch.fnmatch(path_lower, h.lower()))

        score = len(comp_matches) * 2.0 + len(kw_matches) * 1.0 + hint_count
        raw_scores.append(score)

    # Normalize to [0, 1]
    max_score = max(raw_scores) if raw_scores else 0
    normalized = [s / max_score if max_score > 0 else 0.0 for s in raw_scores]

    result = []
    for c, score in zip(candidates, normalized):
        c = dict(c)
        c.setdefault("signals", []).append(
            {
                "filter": "path_relevance",
                "passed": True,
                "score": round(score, 4),
                "reason": f"Path relevance score: {score:.4f}",
            }
        )
        result.append(c)
    return result


def stage_keyword_relevance(candidates: list[dict], task_context: dict) -> list[dict]:
    """Stage 5: Score candidates by keyword relevance using BM25."""
    keywords = task_context.get("keywords", [])
    query_tokens = tokenize(" ".join(keywords))

    # Build corpus from candidate content or file paths
    corpus = []
    for c in candidates:
        text = c.get("content", "") or c.get("file_path", "")
        # Use first 2000 chars of content for efficiency
        if isinstance(text, str) and len(text) > 2000:
            text = text[:2000]
        corpus.append(tokenize(text))

    if not corpus or not query_tokens:
        result = []
        for c in candidates:
            c = dict(c)
            c.setdefault("signals", []).append(
                {
                    "filter": "keyword_relevance",
                    "passed": False,
                    "score": 0.0,
                    "reason": "No content for BM25 scoring",
                }
            )
            result.append(c)
        return result

    bm25 = BM25(corpus)
    raw_scores = bm25.get_scores(query_tokens)

    # Normalize to [0, 1]
    min_s = min(raw_scores)
    max_s = max(raw_scores)
    if max_s > min_s:
        normalized = [(s - min_s) / (max_s - min_s) for s in raw_scores]
    else:
        normalized = [0.0] * len(raw_scores)

    result = []
    for c, score in zip(candidates, normalized):
        c = dict(c)
        c.setdefault("signals", []).append(
            {
                "filter": "keyword_relevance",
                "passed": score > 0.0,
                "score": round(score, 4),
                "reason": f"BM25 score: {score:.4f}",
            }
        )
        result.append(c)
    return result


def composite_score(candidate: dict) -> float:
    """Compute composite score as mean of passed signal scores."""
    signals = candidate.get("signals", [])
    passed_scores = [s["score"] for s in signals if s.get("passed") and s.get("score") is not None]
    if passed_scores:
        return sum(passed_scores) / len(passed_scores)
    return 1.0 if candidate.get("static") else 0.0


def stage_budget_enforcer(candidates: list[dict], token_budget: int) -> list[dict]:
    """Stage 6: Select top-scoring candidates within token budget."""
    for c in candidates:
        c["composite_score"] = composite_score(c)

    # Separate static (always_include) candidates from dynamic ones
    static_candidates = [c for c in candidates if c.get("static")]
    dynamic_candidates = sorted(
        [c for c in candidates if not c.get("static")],
        key=lambda c: c["composite_score"],
        reverse=True,
    )

    def _estimate_tokens(c: dict) -> int:
        content = c.get("content", "")
        if content:
            return len(content) // 4
        elif c.get("size_bytes"):
            return c["size_bytes"] // 4
        return 0

    selected = []
    tokens_used = 0

    # Always include static candidates first, regardless of budget
    for c in static_candidates:
        c = dict(c)
        est_tokens = _estimate_tokens(c)
        c.setdefault("signals", []).append(
            {
                "filter": "budget_enforcer",
                "passed": True,
                "reason": "Static source (always selected first)",
            }
        )
        c["estimated_tokens"] = est_tokens
        selected.append(c)
        tokens_used += est_tokens

    # Then fill remaining budget with dynamic candidates
    for rank, c in enumerate(dynamic_candidates, start=1):
        est_tokens = _estimate_tokens(c)

        if tokens_used + est_tokens <= token_budget:
            c = dict(c)
            c.setdefault("signals", []).append(
                {
                    "filter": "budget_enforcer",
                    "passed": True,
                    "reason": (
                        f"Selected at rank {rank}"
                        f" ({tokens_used + est_tokens}"
                        f"/{token_budget} tokens)"
                    ),
                }
            )
            c["estimated_tokens"] = est_tokens
            selected.append(c)
            tokens_used += est_tokens

    return selected


# --- Pipeline ---


def run_pipeline(data: dict) -> list[dict]:
    """Run the full six-stage filtering pipeline."""
    candidates = data["candidates"]
    task_context = data["task_context"]
    source_declarations = data.get("source_declarations", [])
    raw_token_budget = data.get("token_budget", 100000)
    try:
        token_budget = int(raw_token_budget)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"token_budget must be an integer, got {raw_token_budget!r}") from exc
    if token_budget < 0:
        raise ValueError("token_budget must be >= 0")
    if token_budget > 1_000_000:
        raise ValueError(f"token_budget must be <= 1000000, got {token_budget}")

    # Collect path hints from source declarations
    path_hints = []
    for decl in source_declarations:
        path_hints.extend(decl.get("path_hints", []) or [])

    # Stage 1: Static inclusion
    candidates = stage_static_inclusion(candidates, source_declarations)

    # Stage 2: Version branch resolution is handled externally (by gather-context.sh)
    # The candidates already have the correct git_ref set.

    # Stage 3: Component affinity
    candidates = stage_component_affinity(candidates, task_context, source_declarations)

    # Stage 4: Path relevance
    candidates = stage_path_relevance(candidates, task_context, path_hints)

    # Stage 5: Keyword relevance
    candidates = stage_keyword_relevance(candidates, task_context)

    # Stage 6: Budget enforcement
    candidates = stage_budget_enforcer(candidates, token_budget)

    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Six-stage context filtering pipeline")
    parser.add_argument("--candidates", help="Path to candidates JSON file")
    parser.add_argument("--task-context", help="Path to task context JSON file")
    args = parser.parse_args()

    if args.candidates and args.task_context:
        base_dir = Path.cwd().resolve()
        for path_str in (args.candidates, args.task_context):
            p = Path(path_str)
            if p.is_absolute():
                print(f"Error: absolute path is not allowed: {path_str}", file=sys.stderr)
                sys.exit(1)
            resolved = (base_dir / p).resolve()
            if base_dir not in resolved.parents and resolved != base_dir:
                print(f"Error: path traversal blocked: {path_str}", file=sys.stderr)
                sys.exit(1)
        with open(args.candidates, encoding="utf-8") as f:
            candidates = json.load(f)
        with open(args.task_context, encoding="utf-8") as f:
            task_context = json.load(f)
        data = {"candidates": candidates, "task_context": task_context}
    else:
        data = json.load(sys.stdin)

    result = run_pipeline(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
