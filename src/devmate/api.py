
"""DevMate AI HTTP API for the dashboard."""

import re
import time
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from devmate.clients.github_client import GitHubClient
from devmate.services.repository_cache import repository_cache
from devmate.services.repository_code_analysis import (
    analyze_repository_code as analyze_repository_code_service,
)
from devmate.tools.repository_tools import fetch_repository_snapshot


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="DevMate AI API",
    description="Backend API for the DevMate AI dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# =========================================================
# REQUEST MODELS
# =========================================================

class RepositoryRequest(BaseModel):
    owner: str = Field(min_length=1, max_length=100)
    repo: str = Field(min_length=1, max_length=100)


class QuestionRequest(RepositoryRequest):
    question: str = Field(min_length=1, max_length=5000)
    session_id: str = Field(
        default="web-dashboard",
        min_length=1,
        max_length=100,
    )


# =========================================================
# SHARED SERVICES
# =========================================================

_qa_service = None
_qa_lock = Lock()


def get_qa_service():
    """Initialize RepositoryQA only once."""

    global _qa_service

    if _qa_service is None:
        with _qa_lock:
            if _qa_service is None:
                from devmate.services.repository_qa import RepositoryQA

                print("[API] Initializing RepositoryQA...", flush=True)
                _qa_service = RepositoryQA()

    return _qa_service


# =========================================================
# VALIDATION
# =========================================================

def validate_repository(owner: str, repo: str) -> str:
    """Validate GitHub owner and repository names."""

    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub owner name.",
        )

    if not re.fullmatch(r"[A-Za-z0-9._-]+", repo):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub repository name.",
        )

    return f"{owner}/{repo}"


# =========================================================
# GITHUB HELPERS
# =========================================================

def fetch_snapshot(owner: str, repo: str) -> dict[str, Any]:
    """Fetch a repository snapshot and close the GitHub client."""

    github = GitHubClient()

    try:
        snapshot = fetch_repository_snapshot(
            github=github,
            owner=owner,
            repo=repo,
        )

        if not snapshot:
            raise RuntimeError("GitHub returned an empty repository snapshot.")

        return snapshot

    finally:
        github.close()


# =========================================================
# REPOSITORY ANALYSIS AND CACHE
# =========================================================

def analyze_snapshot(
    github: GitHubClient,
    owner: str,
    repo: str,
    snapshot: dict[str, Any],
):
    """Analyze a snapshot and store the result in the repository cache."""

    repository = f"{owner}/{repo}"

    analysis = analyze_repository_code_service(
        github=github,
        owner=owner,
        repo=repo,
        snapshot=snapshot,
    )

    if not isinstance(analysis, dict):
        raise RuntimeError("Repository analysis returned an invalid result.")

    source_files = analysis.get("source_files")

    if source_files is None:
        raise RuntimeError(
            "Repository analysis did not return source_files."
        )

    repository_cache.set_analysis(
        repository=repository,
        analysis=analysis,
        source_files=source_files,
    )

    return analysis, source_files


def get_or_create_analysis(owner: str, repo: str):
    """Return cached analysis or fetch and analyze the repository."""

    repository = f"{owner}/{repo}"

    analysis = repository_cache.get_analysis(repository)
    source_files = repository_cache.get_source_files(repository)

    if analysis is not None and source_files is not None:
        print(f"[API] Analysis cache hit: {repository}", flush=True)
        return analysis, source_files

    print(f"[API] Analysis cache miss: {repository}", flush=True)

    github = GitHubClient()

    try:
        start = time.perf_counter()

        snapshot = fetch_repository_snapshot(
            github=github,
            owner=owner,
            repo=repo,
        )

        print(
            f"[API] GitHub snapshot fetched in "
            f"{time.perf_counter() - start:.2f}s",
            flush=True,
        )

        if not snapshot:
            raise RuntimeError("Unable to fetch repository snapshot.")

        start = time.perf_counter()

        analysis, source_files = analyze_snapshot(
            github=github,
            owner=owner,
            repo=repo,
            snapshot=snapshot,
        )

        print(
            f"[API] Repository analysis completed in "
            f"{time.perf_counter() - start:.2f}s",
            flush=True,
        )

        return analysis, source_files

    finally:
        github.close()


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health_check():
    """Check whether the API server is running."""

    return {
        "status": "ok",
        "service": "DevMate AI API",
        "version": "1.0.0",
    }


# =========================================================
# CONNECT REPOSITORY
# =========================================================

@app.post("/api/repository/connect")
def connect_repository(request: RepositoryRequest):
    """Check whether a GitHub repository can be accessed."""

    repository = validate_repository(
        request.owner,
        request.repo,
    )

    try:
        snapshot = fetch_snapshot(
            request.owner,
            request.repo,
        )

        return {
            "status": "success",
            "repository": repository,
            "message": "GitHub repository connected successfully.",
            "snapshot_available": bool(snapshot),
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[API] Repository connection failed: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "Unable to access this GitHub repository. "
                "Check the owner, repository name, visibility "
                "and GitHub credentials."
            ),
        ) from exc


# =========================================================
# ANALYZE REPOSITORY
# =========================================================

@app.post("/api/repository/analyze")
def analyze_repository(request: RepositoryRequest):
    """Run AST-based and cross-file repository analysis."""

    repository = validate_repository(
        request.owner,
        request.repo,
    )

    start = time.perf_counter()

    try:
        analysis, source_files = get_or_create_analysis(
            request.owner,
            request.repo,
        )

        files = analysis.get("files", [])

        return {
            "status": "success",
            "repository": repository,
            "summary": analysis.get("summary", {}),
            "files": [
                {
                    "file": item.get("file"),
                    "functions": len(item.get("functions", [])),
                    "classes": len(item.get("classes", [])),
                    "imports": len(item.get("imports", [])),
                    "function_calls": len(
                        item.get("function_calls", [])
                    ),
                }
                for item in files
            ],
            "source_file_count": len(source_files),
            "timings": {
                "total": round(time.perf_counter() - start, 2),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[API] Repository analysis failed: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Repository analysis failed: {str(exc)}",
        ) from exc


# =========================================================
# INDEX REPOSITORY
# =========================================================

@app.post("/api/repository/index")
def index_repository(request: RepositoryRequest):
    """Generate embeddings and index repository code in ChromaDB."""

    repository = validate_repository(
        request.owner,
        request.repo,
    )

    from devmate.services.repository_indexer import RepositoryIndexer

    start = time.perf_counter()
    github = GitHubClient()

    try:
        # 1. Fetch repository snapshot.
        snapshot = fetch_repository_snapshot(
            github=github,
            owner=request.owner,
            repo=request.repo,
        )

        if not snapshot:
            raise RuntimeError("Unable to fetch repository snapshot.")

        # 2. Generate and store vector embeddings.
        indexer = RepositoryIndexer()

        indexing_result = indexer.index_repository(
            github=github,
            owner=request.owner,
            repo=request.repo,
            snapshot=snapshot,
        )

        # 3. Prepare AST analysis using the SAME snapshot.
        # This avoids fetching the repository a second time.
        analysis, source_files = analyze_snapshot(
            github=github,
            owner=request.owner,
            repo=request.repo,
            snapshot=snapshot,
        )

        print(
            f"[API] Indexing and analysis completed for {repository}",
            flush=True,
        )

        return {
            "status": "success",
            "repository": repository,
            "indexing": indexing_result,
            "analysis": {
                "source_file_count": len(source_files),
                "analyzed_file_count": len(analysis.get("files", [])),
            },
            "timings": {
                "total": round(time.perf_counter() - start, 2),
            },
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[API] Repository indexing failed: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Repository indexing failed: {str(exc)}",
        ) from exc

    finally:
        github.close()


# =========================================================
# ASK REPOSITORY QUESTION
# =========================================================

@app.post("/api/repository/ask")
def ask_repository_question(request: QuestionRequest):
    """Answer questions using repository context and Gemini."""

    repository = validate_repository(
        request.owner,
        request.repo,
    )

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    start = time.perf_counter()

    try:
        # 1. Get repository analysis and source files.
        analysis, source_files = get_or_create_analysis(
            request.owner,
            request.repo,
        )

        # 2. Initialize the Q&A service.
        qa = get_qa_service()

        # 3. Retrieve context and generate the answer.
        result = qa.answer(
            analysis=analysis,
            source_files=source_files,
            question=question,
            repository=repository,
            max_contexts=8,
            session_id=request.session_id,
        )

        if not isinstance(result, dict):
            raise RuntimeError("RepositoryQA returned an invalid response.")

        result["api_timings"] = {
            "total": round(time.perf_counter() - start, 2),
        }

        return result

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[API] Question answering failed: {exc}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Unable to answer repository question: {str(exc)}",
        ) from exc
