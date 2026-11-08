
"""Contextual code retrieval for DevMate AI."""

import re
from typing import Any

from devmate.services.code_search import (
    search_symbols,
    search_imports,
    search_code_keywords,
    search_files,
)


# ============================================================
# BASIC HELPERS
# ============================================================

def _normalize(value: str) -> str:
    return value.strip().lower()


def _get_source_map(
    source_files: list[dict[str, Any]],
) -> dict[str, str]:
    """Build a mapping of repository paths to source content."""

    return {
        item["path"]: item.get("content", "")
        for item in source_files
        if item.get("path")
    }


def _get_file_analysis(
    analysis: dict[str, Any],
    file_path: str,
) -> dict[str, Any] | None:
    """Find a file's AST analysis."""

    for item in analysis.get("files", []):
        if item.get("file") == file_path:
            return item

    return None


def _get_cross_file_analysis(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    return analysis.get("cross_file_analysis", {}) or {}


def _get_module_relationships(
    analysis: dict[str, Any],
) -> dict[str, Any]:
    return analysis.get("module_relationships", {}) or {}


def _is_test_file(file_path: str) -> bool:
    """Identify test files so production code can be prioritized."""

    normalized = file_path.replace("\\", "/").lower()
    filename = normalized.split("/")[-1]

    return (
        normalized.startswith("tests/")
        or "/tests/" in normalized
        or filename.startswith("test_")
        or filename.endswith("_test.py")
    )


def _adjust_score(
    score: int,
    file_path: str,
) -> int:
    """Prioritize production code over test code."""

    if _is_test_file(file_path):
        return score - 2

    return score + 1


def _extract_terms(query: str) -> list[str]:
    """Extract meaningful search terms from a natural-language query."""

    ignored_words = {
        "what", "where", "when", "which", "who",
        "how", "does", "do", "did", "is", "are",
        "was", "were", "the", "a", "an", "and",
        "or", "to", "of", "in", "on", "for",
        "with", "from", "this", "that", "it",
        "explain", "show", "tell", "me", "about",
        "work", "works", "working",
        "devmate", "retrieve", "retrieves",
        "retrieving", "code", "repository",
        "file", "files", "function", "functions",
        "please", "can", "could", "would",
        "using", "use", "used", "within",
    }

    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query)

    terms = []
    seen = set()

    for word in words:
        normalized = _normalize(word)

        if normalized in ignored_words:
            continue

        if len(normalized) < 2 or normalized in seen:
            continue

        seen.add(normalized)
        terms.append(word)

    return terms


# ============================================================
# SOURCE CODE EXTRACTION
# ============================================================

def extract_source_context(
    source_files: list[dict[str, Any]],
    file_path: str,
    start_line: int,
    end_line: int,
    padding: int = 2,
) -> dict[str, Any] | None:
    """Extract a source-code section with surrounding lines."""

    source_map = _get_source_map(source_files)
    content = source_map.get(file_path)

    if content is None:
        return None

    lines = content.splitlines()

    if not lines:
        return None

    start = max(1, start_line - padding)
    end = min(len(lines), end_line + padding)

    snippet = "\n".join(
        f"{line_number}: {lines[line_number - 1]}"
        for line_number in range(start, end + 1)
    )

    return {
        "file": file_path,
        "start_line": start,
        "end_line": end,
        "snippet": snippet,
    }


def _extract_line_context(
    source_files: list[dict[str, Any]],
    file_path: str,
    line: int,
    padding: int = 2,
) -> dict[str, Any] | None:
    return extract_source_context(
        source_files,
        file_path,
        line,
        line,
        padding,
    )


# ============================================================
# CONTEXT COLLECTION
# ============================================================

def _make_context_record(
    source_files: list[dict[str, Any]],
    file_path: str,
    start_line: int,
    end_line: int,
    context_type: str,
    symbol: str | None = None,
    padding: int = 2,
) -> dict[str, Any] | None:
    """Create a context record with source code."""

    source = extract_source_context(
        source_files,
        file_path,
        start_line,
        end_line,
        padding,
    )

    if source is None:
        return None

    return {
        **source,
        "type": context_type,
        "symbol": symbol,
    }


def _deduplicate_context(
    contexts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove duplicate source sections, retaining the highest score."""

    unique = {}

    for context in contexts:
        key = (
            context["file"],
            context["start_line"],
            context["end_line"],
        )

        existing = unique.get(key)

        if (
            existing is None
            or context.get("score", 0) > existing.get("score", 0)
        ):
            unique[key] = context

    return list(unique.values())


# ============================================================
# SYMBOL CONTEXT
# ============================================================

def retrieve_symbol_context(
    analysis: dict[str, Any],
    source_files: list[dict[str, Any]],
    symbol_name: str,
) -> list[dict[str, Any]]:
    """Retrieve definitions of a function, class, or method."""

    definitions = search_symbols(
        analysis,
        symbol_name,
        exact=True,
    )

    contexts = []

    for definition in definitions:
        context = _make_context_record(
            source_files=source_files,
            file_path=definition["file"],
            start_line=definition["line"],
            end_line=definition.get("end_line") or definition["line"],
            context_type="symbol_definition",
            symbol=definition["name"],
        )

        if context:
            contexts.append(context)

    return contexts


# ============================================================
# REFERENCE CONTEXT
# ============================================================

def retrieve_reference_context(
    analysis: dict[str, Any],
    source_files: list[dict[str, Any]],
    symbol_name: str,
) -> list[dict[str, Any]]:
    """Retrieve locations where a symbol is called or referenced."""

    cross_file = _get_cross_file_analysis(analysis)

    references = (
        cross_file.get("references", [])
        + cross_file.get("unresolved_references", [])
    )

    contexts = []
    normalized_query = _normalize(symbol_name)

    for reference in references:
        name = reference.get("name", "")
        qualified_name = reference.get("qualified_name", "")

        if (
            _normalize(name) != normalized_query
            and _normalize(qualified_name) != normalized_query
        ):
            continue

        source_path = (
            reference.get("source")
            or reference.get("source_file")
        )

        line = reference.get("line") or reference.get("call_line")

        if not source_path or not line:
            continue

        context = _make_context_record(
            source_files=source_files,
            file_path=source_path,
            start_line=line,
            end_line=line,
            context_type=(
                "resolved_reference"
                if reference.get("resolved")
                else "unresolved_reference"
            ),
            symbol=qualified_name or name,
        )

        if context:
            context["reference_type"] = reference.get(
                "reference_type"
            )
            context["target"] = reference.get("target")
            contexts.append(context)

    return _deduplicate_context(contexts)


# ============================================================
# IMPORT CONTEXT
# ============================================================

def retrieve_import_context(
    analysis: dict[str, Any],
    source_files: list[dict[str, Any]],
    query: str,
) -> list[dict[str, Any]]:
    """Retrieve relevant import statements."""

    imports = search_imports(analysis, query)
    contexts = []

    for imported in imports:
        file_path = imported["file"]
        line = imported.get("line")

        if not line:
            continue

        context = _make_context_record(
            source_files=source_files,
            file_path=file_path,
            start_line=line,
            end_line=line,
            context_type="import",
            symbol=imported.get("name"),
        )

        if context:
            contexts.append(context)

    return _deduplicate_context(contexts)


# ============================================================
# RELATED FILE CONTEXT
# ============================================================

def retrieve_related_file_context(
    analysis: dict[str, Any],
    source_files: list[dict[str, Any]],
    file_path: str,
) -> list[dict[str, Any]]:
    """Retrieve files directly connected to a given file."""

    related_paths = set()

    # Direct module dependencies.
    for dependency in _get_module_relationships(
        analysis
    ).get("dependencies", []):

        source = dependency.get("source")
        target = dependency.get("target")

        if source == file_path and target:
            related_paths.add(target)

        elif target == file_path and source:
            related_paths.add(source)

    # Direct resolved cross-file references.
    cross_file = _get_cross_file_analysis(analysis)

    for reference in cross_file.get("references", []):
        source = (
            reference.get("source")
            or reference.get("source_file")
        )
        target = reference.get("target")

        if source == file_path and target:
            related_paths.add(target)

        elif target == file_path and source:
            related_paths.add(source)

    # Reverse import relationships.
    for item in cross_file.get("imported_by", []):
        target = item.get("target_file")

        if target == file_path:
            for reference in item.get("references", []):
                source = (
                    reference.get("source")
                    or reference.get("file")
                )

                if source:
                    related_paths.add(source)

    source_map = _get_source_map(source_files)

    return [
        {
            "file": path,
            "type": "related_file",
            "content_available": path in source_map,
        }
        for path in sorted(related_paths)
        if path != file_path
    ]


# ============================================================
# QUERY CONTEXT
# ============================================================

def retrieve_query_context(
    analysis: dict[str, Any],
    source_files: list[dict[str, Any]],
    query: str,
    max_contexts: int = 20,
    padding: int = 2,
) -> dict[str, Any]:
    """
    Retrieve relevant code context for a natural-language query.

    Combines symbol, reference, import, file and keyword searches.
    Production definitions and direct references receive higher priority.
    """

    if not query or not query.strip():
        return {
            "query": query,
            "total_contexts": 0,
            "total_candidates": 0,
            "contexts": [],
            "related_files": [],
            "search_terms": [],
        }

    terms = _extract_terms(query)

    contexts = []
    related_paths = set()

    for term in terms:

        # ----------------------------------------------------
        # 1. Symbol definitions
        # ----------------------------------------------------

        symbol_results = search_symbols(
            analysis,
            term,
        )

        for result in symbol_results:
            context = _make_context_record(
                source_files,
                result["file"],
                result["line"],
                result.get("end_line") or result["line"],
                "symbol_definition",
                result["name"],
                padding,
            )

            if context:
                is_exact = (
                    _normalize(result["name"]) == _normalize(term)
                )

                base_score = 8 if is_exact else 5

                context["score"] = _adjust_score(
                    base_score,
                    context["file"],
                )

                context["matched_term"] = term
                contexts.append(context)

        # ----------------------------------------------------
        # 2. Resolved and unresolved references
        # ----------------------------------------------------

        reference_results = retrieve_reference_context(
            analysis,
            source_files,
            term,
        )

        for context in reference_results:
            if context.get("type") == "resolved_reference":
                base_score = 6
            else:
                base_score = 3

            context["score"] = _adjust_score(
                base_score,
                context["file"],
            )

            context["matched_term"] = term
            contexts.append(context)

        # ----------------------------------------------------
        # 3. Import statements
        # ----------------------------------------------------

        import_results = retrieve_import_context(
            analysis,
            source_files,
            term,
        )

        for context in import_results:
            context["score"] = _adjust_score(
                3,
                context["file"],
            )

            context["matched_term"] = term
            contexts.append(context)

        # ----------------------------------------------------
        # 4. Keyword matches in source code
        # ----------------------------------------------------

        keyword_results = search_code_keywords(
            source_files,
            term,
        )

        for result in keyword_results:
            context = _make_context_record(
                source_files,
                result["file"],
                result["line"],
                result["line"],
                "keyword_match",
                term,
                padding,
            )

            if context:
                context["score"] = _adjust_score(
                    1,
                    context["file"],
                )

                context["matched_term"] = term
                contexts.append(context)

        # ----------------------------------------------------
        # 5. File path matches
        # ----------------------------------------------------

        file_results = search_files(
            analysis,
            term,
        )

        for result in file_results:
            related_paths.add(result["file"])

    # --------------------------------------------------------
    # 6. Deduplicate and rank contexts
    # --------------------------------------------------------

    contexts = _deduplicate_context(contexts)

    contexts.sort(
        key=lambda item: (
            -item.get("score", 0),
            item["file"],
            item["start_line"],
        )
    )

    # Keep the original candidate count before limiting.
    total_candidates = len(contexts)

    selected_contexts = contexts[:max_contexts]

    # --------------------------------------------------------
    # 7. Collect related-file metadata
    # --------------------------------------------------------

    # Only inspect relationships of selected contexts.
    # Related files are metadata, not automatically retrieved
    # source-code contexts.

    for context in selected_contexts:
        related_results = retrieve_related_file_context(
            analysis,
            source_files,
            context["file"],
        )

        for related in related_results:
            related_paths.add(related["file"])

    source_map = _get_source_map(source_files)

    # Exclude files already represented by selected contexts.
    selected_paths = {
        context["file"]
        for context in selected_contexts
    }

    related_paths.difference_update(selected_paths)

    related_files = [
        {
            "file": path,
            "content_available": path in source_map,
        }
        for path in sorted(related_paths)
    ]

    return {
        "query": query,
        "search_terms": terms,
        "total_contexts": len(selected_contexts),
        "total_candidates": total_candidates,
        "contexts": selected_contexts,
        "related_files": related_files,
    }


# ============================================================
# CONTEXT PACKAGE
# ============================================================

def build_context_package(
    analysis: dict[str, Any],
    source_files: list[dict[str, Any]],
    query: str,
    max_contexts: int = 20,
) -> dict[str, Any]:
    """Build a structured package for the repository Q&A engine."""

    context_result = retrieve_query_context(
        analysis=analysis,
        source_files=source_files,
        query=query,
        max_contexts=max_contexts,
    )

    return {
        "repository": analysis.get("repository"),
        "question": query,
        "context_count": context_result["total_contexts"],
        "search_terms": context_result["search_terms"],
        "code_context": context_result["contexts"],
        "related_files": context_result["related_files"],
        "insufficient_context": (
            context_result["total_contexts"] == 0
        ),
    }
