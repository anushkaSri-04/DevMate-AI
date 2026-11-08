
"""In-memory cache for indexed repository data."""

from threading import RLock
from typing import Any


class RepositoryCache:
    """Cache repository source files and AST analysis."""

    def __init__(self) -> None:
        self._repositories: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _normalize(repository: str) -> str:
        return repository.strip().lower()

    def set_source_files(
        self,
        repository: str,
        source_files: list[dict[str, Any]],
    ) -> None:
        key = self._normalize(repository)

        with self._lock:
            entry = self._repositories.setdefault(key, {})
            entry["source_files"] = source_files

    def get_source_files(
        self,
        repository: str,
    ) -> list[dict[str, Any]] | None:
        key = self._normalize(repository)

        with self._lock:
            entry = self._repositories.get(key)
            return entry.get("source_files") if entry else None

    def set_analysis(
        self,
        repository: str,
        analysis: dict[str, Any],
        source_files: list[dict[str, Any]],
    ) -> None:
        key = self._normalize(repository)

        with self._lock:
            self._repositories[key] = {
                "analysis": analysis,
                "source_files": source_files,
            }

    def get_analysis(
        self,
        repository: str,
    ) -> dict[str, Any] | None:
        key = self._normalize(repository)

        with self._lock:
            entry = self._repositories.get(key)
            return entry.get("analysis") if entry else None

    def invalidate_repository(self, repository: str) -> None:
        key = self._normalize(repository)

        with self._lock:
            self._repositories.pop(key, None)

    def has_analysis(self, repository: str) -> bool:
        return self.get_analysis(repository) is not None


# Shared cache instance across the MCP server services.
repository_cache = RepositoryCache()
