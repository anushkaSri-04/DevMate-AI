
"""DevMate AI MCP server."""

import time

from mcp.server import MCPServer

from devmate.services.project_profile import get_project_profile
from devmate.services.repository_cache import repository_cache

from devmate.services.repository_code_analysis import (
    get_repository_code_analysis,
    analyze_repository_code as analyze_repository_code_service,
)

from devmate.tools.github_tools import (
    count_open_issues as github_count_open_issues,
    get_repository_details as github_get_repository_details,
    list_issues as github_list_issues,
    list_repositories as github_list_repositories,
)

from devmate.tools.repository_tools import (
    analyze_repository_dependencies,
    analyze_repository_structure,
    fetch_repository_snapshot,
)

from devmate.clients.github_client import GitHubClient


# --------------------------------------------------
# MCP SERVER
# --------------------------------------------------

mcp = MCPServer("DevMate AI")


# --------------------------------------------------
# PERSISTENT QA SERVICE
# --------------------------------------------------

_repository_qa = None


def get_qa_service():
    """Create one QA instance and reuse it across requests."""

    global _repository_qa

    if _repository_qa is None:
        from devmate.services.repository_qa import RepositoryQA

        print("[DevMate] Initializing RepositoryQA...", flush=True)

        start = time.perf_counter()

        _repository_qa = RepositoryQA()

        print(
            f"[DevMate] RepositoryQA initialized in "
            f"{time.perf_counter() - start:.2f}s",
            flush=True,
        )

    return _repository_qa


# --------------------------------------------------
# GITHUB TOOLS
# --------------------------------------------------

@mcp.tool()
def list_repositories() -> list[dict]:
    """List repositories belonging to the authenticated GitHub user."""

    return github_list_repositories()


@mcp.tool()
def get_repository_details(owner: str, repo: str) -> dict:
    """Get details of a specific GitHub repository."""

    return github_get_repository_details(owner, repo)


@mcp.tool()
def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 30,
    max_pages: int = 5,
) -> dict:
    """List issues in a GitHub repository."""

    issues, complete = github_list_issues(
        owner=owner,
        repo=repo,
        state=state,
        per_page=per_page,
        max_pages=max_pages,
    )

    return {
        "issues": issues,
        "complete": complete,
        "count": len(issues),
    }


@mcp.tool()
def count_open_issues(owner: str, repo: str) -> dict:
    """Count open issues in a GitHub repository."""

    return github_count_open_issues(owner, repo)


# --------------------------------------------------
# REPOSITORY TOOLS
# --------------------------------------------------

@mcp.tool()
def analyze_repository(owner: str, repo: str) -> dict:
    """Analyze repository file and directory structure."""

    return analyze_repository_structure(
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def analyze_dependencies(owner: str, repo: str) -> dict:
    """Analyze dependencies declared in a GitHub repository."""

    return analyze_repository_dependencies(
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def get_project_profile_tool(owner: str, repo: str) -> dict:
    """Generate a unified profile of a GitHub repository."""

    return get_project_profile(
        owner=owner,
        repo=repo,
    )


@mcp.tool()
def analyze_repository_code_tool(
    owner: str,
    repo: str,
) -> dict:
    """Analyze Python files, functions, classes, imports and calls."""

    return get_repository_code_analysis(
        owner=owner,
        repo=repo,
    )


# --------------------------------------------------
# REPOSITORY INDEXING
# --------------------------------------------------

@mcp.tool()
def index_repository_code(owner: str, repo: str) -> dict:
    """
    Index Python repository code for semantic search
    and contextual retrieval.
    """

    from devmate.services.repository_indexer import RepositoryIndexer

    repository = f"{owner}/{repo}"

    print(
        f"\n[DevMate] Starting indexing: {repository}",
        flush=True,
    )

    start = time.perf_counter()

    github = GitHubClient()

    try:
        snapshot_start = time.perf_counter()

        snapshot = fetch_repository_snapshot(
            github,
            owner,
            repo,
        )

        print(
            f"[Timing] GitHub snapshot: "
            f"{time.perf_counter() - snapshot_start:.2f}s",
            flush=True,
        )

        indexer = RepositoryIndexer()

        result = indexer.index_repository(
            github=github,
            owner=owner,
            repo=repo,
            snapshot=snapshot,
        )

        print(
            f"[Timing] Total indexing: "
            f"{time.perf_counter() - start:.2f}s",
            flush=True,
        )

        return result

    finally:
        github.close()


# --------------------------------------------------
# REPOSITORY QUESTION ANSWERING
# --------------------------------------------------

@mcp.tool()
def ask_repository_question(
    owner: str,
    repo: str,
    question: str,
    session_id: str = "default",
) -> dict:
    """
    Answer natural-language questions about a Python GitHub repository
    using cached AST analysis, hybrid retrieval, source evidence and Gemini.

    Run index_repository_code before asking questions.
    """

    if not question or not question.strip():
        return {
            "status": "error",
            "message": "Question cannot be empty.",
        }

    repository = f"{owner}/{repo}"

    total_start = time.perf_counter()

    print(
        f"\n[DevMate] Question received: {question}",
        flush=True,
    )

    # ----------------------------------------------
    # 1. CHECK REPOSITORY CACHE
    # ----------------------------------------------

    analysis = repository_cache.get_analysis(repository)

    source_files = repository_cache.get_source_files(repository)

    if analysis is None or source_files is None:

        print(
            f"[DevMate] Cache miss: {repository}",
            flush=True,
        )

        github = GitHubClient()

        try:
            # Fetch GitHub snapshot.
            start = time.perf_counter()

            snapshot = fetch_repository_snapshot(
                github,
                owner,
                repo,
            )

            print(
                f"[Timing] GitHub snapshot: "
                f"{time.perf_counter() - start:.2f}s",
                flush=True,
            )

            # Perform AST and cross-file analysis.
            start = time.perf_counter()

            analysis = analyze_repository_code_service(
                github=github,
                owner=owner,
                repo=repo,
                snapshot=snapshot,
            )

            print(
                f"[Timing] AST analysis: "
                f"{time.perf_counter() - start:.2f}s",
                flush=True,
            )

            source_files = analysis.get("source_files")

            if source_files is None:
                source_files = repository_cache.get_source_files(
                    repository
                )

            if source_files is None:
                return {
                    "status": "error",
                    "message": (
                        "Source files are missing. "
                        "Check that repository analysis returns "
                        "the source_files field."
                    ),
                }

            # Cache analysis and source files.
            repository_cache.set_analysis(
                repository=repository,
                analysis=analysis,
                source_files=source_files,
            )

        finally:
            github.close()

    else:
        print(
            f"[DevMate] Cache hit: {repository}",
            flush=True,
        )

        print(
            "[DevMate] Reusing cached repository analysis.",
            flush=True,
        )

    # ----------------------------------------------
    # 2. INITIALIZE QA SERVICE
    # ----------------------------------------------

    qa = get_qa_service()

    # ----------------------------------------------
    # 3. HYBRID RETRIEVAL + EVIDENCE + GEMINI
    # ----------------------------------------------

    start = time.perf_counter()

    result = qa.answer(
        analysis=analysis,
        source_files=source_files,
        question=question,
        repository=repository,
        max_contexts=8,
        session_id=session_id,
    )

    print(
        f"[Timing] Retrieval + Gemini Q&A: "
        f"{time.perf_counter() - start:.2f}s",
        flush=True,
    )

    print(
        f"[Timing] Total question processing: "
        f"{time.perf_counter() - total_start:.2f}s",
        flush=True,
    )

    return result


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":
    print(
        "Starting DevMate AI MCP Server...",
        flush=True,
    )

    mcp.run()
