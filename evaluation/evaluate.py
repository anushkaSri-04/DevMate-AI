"""Evaluate DevMate AI lexical, semantic and hybrid code retrieval.

Run from the DevMate-AI project root:
    python -m evaluation.evaluate

Requires an already indexed ChromaDB collection for the target repository.
No source code or vector-index data is modified.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

K_VALUES = (5, 10, 20)


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").removeprefix("./").strip().lower()


def overlaps(result: dict[str, Any], gold: dict[str, Any]) -> bool:
    """Match the same file and at least one overlapping source line."""
    if normalize_path(str(result.get("file", ""))) != normalize_path(gold["file"]):
        return False
    try:
        start, end = int(result["start_line"]), int(result["end_line"])
    except (KeyError, TypeError, ValueError):
        return False
    return start <= gold["end_line"] and end >= gold["start_line"]


def matched_gold_ids(
    retrieved: list[dict[str, Any]],
    gold: list[dict[str, Any]],
    k: int,
) -> set[int]:
    return {
        i
        for i, section in enumerate(gold)
        if any(overlaps(result, section) for result in retrieved[:k])
    }


def recall_at_k(retrieved: list[dict[str, Any]], gold: list[dict[str, Any]], k: int) -> float:
    if not gold:
        raise ValueError("Recall requires at least one gold section")
    return len(matched_gold_ids(retrieved, gold, k)) / len(gold)


def reciprocal_rank_at_k(
    retrieved: list[dict[str, Any]], gold: list[dict[str, Any]], k: int
) -> float:
    for rank, result in enumerate(retrieved[:k], start=1):
        if any(overlaps(result, section) for section in gold):
            return 1.0 / rank
    return 0.0


def ndcg_at_k(
    retrieved: list[dict[str, Any]], gold: list[dict[str, Any]], k: int
) -> float:
    """Binary nDCG; credit each gold section at most once."""
    if not gold:
        raise ValueError("nDCG requires at least one gold section")
    used_gold: set[int] = set()
    dcg = 0.0
    for rank, result in enumerate(retrieved[:k], start=1):
        first_new = next(
            (i for i, section in enumerate(gold)
             if i not in used_gold and overlaps(result, section)),
            None,
        )
        if first_new is not None:
            used_gold.add(first_new)
            dcg += 1.0 / math.log2(rank + 1)
    ideal = sum(1.0 / math.log2(rank + 1) for rank in range(1, min(k, len(gold)) + 1))
    return dcg / ideal if ideal else 0.0


def read_questions(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        questions = json.load(file)
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions.json must be a nonempty JSON array")
    ids: set[str] = set()
    for item in questions:
        question_id = str(item.get("id", ""))
        if not question_id or question_id in ids:
            raise ValueError(f"Missing or duplicate question ID: {question_id!r}")
        ids.add(question_id)
        if not isinstance(item.get("query"), str) or not item["query"].strip():
            raise ValueError(f"Question {question_id} has no query")
        sections = item.get("relevant_sections")
        if not isinstance(sections, list) or not sections:
            raise ValueError(f"Question {question_id} needs manually verified relevant_sections")
        for section in sections:
            if not isinstance(section.get("file"), str) or not section["file"]:
                raise ValueError(f"Question {question_id} has a missing file path")
            for field in ("start_line", "end_line"):
                if type(section.get(field)) is not int or section[field] < 1:
                    raise ValueError(f"Question {question_id} has an invalid {field}")
            if section["end_line"] < section["start_line"]:
                raise ValueError(f"Question {question_id} has an inverted line range")
    return questions


def validate_gold_against_source(
    questions: list[dict[str, Any]], source_files: list[dict[str, Any]]
) -> None:
    """Fail early if the labels are stale relative to the fetched GitHub snapshot."""
    source_map = {
        normalize_path(item["path"]): item.get("content", "")
        for item in source_files if item.get("path")
    }
    for question in questions:
        for section in question["relevant_sections"]:
            key = normalize_path(section["file"])
            if key not in source_map:
                raise ValueError(f"Q{question['id']}: labelled file absent from GitHub snapshot: {section['file']}")
            lines = source_map[key].splitlines()
            if section["end_line"] > len(lines):
                raise ValueError(f"Q{question['id']}: labelled range exceeds {section['file']} ({len(lines)} lines)")
            anchor = section.get("anchor")
            if anchor and anchor not in "\n".join(lines[section["start_line"] - 1:section["end_line"]]):
                raise ValueError(
                    f"Q{question['id']}: source has changed; anchor {anchor!r} not found in "
                    f"{section['file']}:{section['start_line']}-{section['end_line']}"
                )


def semantic_contexts(
    vector_store: Any,
    embedding_service: Any,
    repository: str,
    query: str,
    source_files: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    from devmate.services.context_retrieval import extract_source_context

    embedding = embedding_service.embed_query(query)
    matches = vector_store.search(
        repository=repository, query_embedding=embedding, top_k=top_k
    )
    contexts: list[dict[str, Any]] = []
    for match in matches:
        metadata = match.get("metadata") or {}
        path = metadata.get("file")
        start, end = metadata.get("start_line"), metadata.get("end_line")
        if not path or start is None or end is None:
            continue
        try:
            source = extract_source_context(
                source_files=source_files,
                file_path=path,
                start_line=int(start),
                end_line=int(end),
                padding=2,
            )
        except (TypeError, ValueError):
            continue
        if source is not None:
            contexts.append({**source, "symbol": metadata.get("symbol"), "vector_chunk_id": match.get("id")})
    return contexts


def compact_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rank": rank,
            "file": context.get("file"),
            "start_line": context.get("start_line"),
            "end_line": context.get("end_line"),
            "symbol": context.get("symbol"),
            "retrieval_sources": context.get("retrieval_sources", []),
        }
        for rank, context in enumerate(contexts, 1)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="anushkaSri-04/DevMate-AI")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/questions.json"))
    parser.add_argument("--chroma-dir", default="data/chroma")
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/results"))
    args = parser.parse_args()

    # Delay project imports so pure metric functions can be tested independently.
    from devmate.clients.github_client import GitHubClient
    from devmate.services.source_code import retrieve_python_source_files
    from devmate.services.repository_code_analysis import analyze_repository_code
    from devmate.services.context_retrieval import build_context_package
    from devmate.services.embedding_service import EmbeddingService
    from devmate.services.vector_store import VectorStore
    from devmate.services.hybrid_retrieval import HybridRetriever
    from devmate.tools.repository_tools import fetch_repository_snapshot

    questions = read_questions(args.questions)
    owner, sep, repo = args.repository.partition("/")
    if not sep or not owner or not repo or "/" in repo:
        parser.error("--repository must be OWNER/REPO")

    vector_store = VectorStore(persist_directory=args.chroma_dir)
    indexed_chunks = vector_store.count_chunks(args.repository)
    if indexed_chunks == 0:
        raise SystemExit(
            f"No indexed chunks for {args.repository!r} in {args.chroma_dir!r}. "
            "Index the same repository from the DevMate dashboard first."
        )
    print(f"Found {indexed_chunks} indexed chunks for {args.repository}")

    github = GitHubClient()
    try:
        snapshot = fetch_repository_snapshot(github, owner, repo)
        source_result = retrieve_python_source_files(github, owner, repo, snapshot)
        source_files = source_result["files"]
        analysis = analyze_repository_code(github, owner, repo, snapshot)
    finally:
        github.close()

    validate_gold_against_source(questions, source_files)
    embedding_service = EmbeddingService()
    hybrid_retriever = HybridRetriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )
    max_k = max(K_VALUES)
    methods = ("lexical", "semantic", "hybrid_rrf")
    rows: list[dict[str, Any]] = []
    ranked: list[dict[str, Any]] = []

    for number, question in enumerate(questions, 1):
        query = question["query"]
        gold = question["relevant_sections"]
        lexical = build_context_package(
            analysis=analysis,
            source_files=source_files,
            query=query,
            max_contexts=max_k * 2,
        )["code_context"][:max_k]
        semantic = semantic_contexts(
            vector_store=vector_store,
            embedding_service=embedding_service,
            repository=args.repository,
            query=query,
            source_files=source_files,
            top_k=max_k,
        )
        hybrid = hybrid_retriever.retrieve(
            analysis=analysis,
            source_files=source_files,
            query=query,
            repository=args.repository,
            max_contexts=max_k,
            semantic_top_k=max_k,
        )["contexts"]
        results_by_method = {
            "lexical": lexical,
            "semantic": semantic,
            "hybrid_rrf": hybrid,
        }
        for method in methods:
            contexts = results_by_method[method]
            row: dict[str, Any] = {
                "id": question["id"],
                "query": query,
                "method": method,
                "gold_sections": len(gold),
                "retrieved": len(contexts),
            }
            for k in K_VALUES:
                row[f"recall@{k}"] = round(recall_at_k(contexts, gold, k), 6)
            row["mrr@10"] = round(reciprocal_rank_at_k(contexts, gold, 10), 6)
            row["ndcg@10"] = round(ndcg_at_k(contexts, gold, 10), 6)
            rows.append(row)
            ranked.append({
                "id": question["id"], "query": query, "method": method,
                "ranked_results": compact_contexts(contexts),
            })
        print(f"[{number}/{len(questions)}] {query}")

    score_names = [*(f"recall@{k}" for k in K_VALUES), "mrr@10", "ndcg@10"]
    summary = {
        "repository": args.repository,
        "questions": len(questions),
        "indexed_chunks": indexed_chunks,
        "matching_rule": "same file and at least one overlapping line; each gold section counted once",
        "metrics": {
            method: {
                score: round(sum(row[score] for row in rows if row["method"] == method) / len(questions), 4)
                for score in score_names
            }
            for method in methods
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "per_query.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (args.output_dir / "ranked_results.json").write_text(json.dumps(ranked, indent=2), encoding="utf-8")

    print("\nMEAN RETRIEVAL METRICS (0 to 1)")
    print(f"{'Method':<14} " + " ".join(f"{name:>11}" for name in score_names))
    for method in methods:
        metrics = summary["metrics"][method]
        print(f"{method:<14} " + " ".join(f"{metrics[name]:>11.4f}" for name in score_names))
    print(f"\nSaved reports to: {args.output_dir}")


if __name__ == "__main__":
    main()
