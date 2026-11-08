
"""Builds clean, structured evidence from repository retrieval contexts."""

from typing import Any


class EvidenceBuilder:
    """Normalize, validate, and deduplicate retrieved code evidence."""

    @staticmethod
    def _normalize_path(file_path: Any) -> str:
        """Normalize repository paths to use forward slashes."""
        if not isinstance(file_path, str):
            return ""

        return file_path.strip().replace("\\", "/").lstrip("./")

    @staticmethod
    def _normalize_sources(sources: Any) -> list[str]:
        """Normalize retrieval source labels."""
        if not isinstance(sources, (list, tuple, set)):
            return []

        return sorted({
            source.strip()
            for source in sources
            if isinstance(source, str) and source.strip()
        })

    @staticmethod
    def _valid_line_range(start_line: Any, end_line: Any) -> bool:
        """Check whether the supplied line range is valid."""
        return (
            isinstance(start_line, int)
            and not isinstance(start_line, bool)
            and isinstance(end_line, int)
            and not isinstance(end_line, bool)
            and start_line >= 1
            and end_line >= start_line
        )

    def _normalize_context(self, context: dict[str, Any]) -> dict[str, Any] | None:
        """Convert one retrieved context into a consistent evidence record."""
        if not isinstance(context, dict):
            return None

        file_path = self._normalize_path(context.get("file"))
        snippet = context.get("snippet")

        if not file_path or not isinstance(snippet, str) or not snippet.strip():
            return None

        start_line = context.get("start_line")
        end_line = context.get("end_line")

        if not self._valid_line_range(start_line, end_line):
            return None

        symbol = context.get("symbol")
        if not isinstance(symbol, str):
            symbol = None

        return {
            "file": file_path,
            "symbol": symbol,
            "start_line": start_line,
            "end_line": end_line,
            "snippet": snippet.strip(),
            "retrieval_sources": self._normalize_sources(
                context.get("retrieval_sources", [])
            ),
        }

    def build(self, contexts: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Build a deduplicated evidence package.

        Contexts are expected to come from HybridRetriever.
        """
        if not isinstance(contexts, list):
            raise TypeError("contexts must be a list")

        evidence = []
        seen = {}

        invalid_count = 0
        duplicate_count = 0

        for context in contexts:
            normalized = self._normalize_context(context)

            if normalized is None:
                invalid_count += 1
                continue

            key = (
                normalized["file"],
                normalized["start_line"],
                normalized["end_line"],
            )

            if key in seen:
                duplicate_count += 1

                # Preserve all retrieval methods that found this evidence.
                existing = seen[key]
                existing["retrieval_sources"] = sorted(
                    set(existing["retrieval_sources"])
                    | set(normalized["retrieval_sources"])
                )
                continue

            seen[key] = normalized
            evidence.append(normalized)

        related_files = sorted({
            item["file"] for item in evidence
        })

        return {
            "evidence": evidence,
            "total_evidence": len(evidence),
            "invalid_contexts": invalid_count,
            "duplicate_contexts": duplicate_count,
            "related_files": related_files,
        }
