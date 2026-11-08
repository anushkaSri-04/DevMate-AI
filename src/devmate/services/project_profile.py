
from devmate.clients.github_client import GitHubClient
from devmate.tools.repository_tools import (
    build_repository_dependencies,
    build_repository_structure,
    fetch_repository_snapshot,
)


def detect_project_type(
    languages: dict[str, int],
    technologies: dict[str, list[str]],
) -> str:
    """Infer a broad project type from languages and technologies."""

    if "Machine Learning" in technologies or "Deep Learning" in technologies:
        return "Machine Learning Project"

    if "LLM Framework" in technologies or "AI Tool Integration" in technologies:
        return "AI Application"

    if "Backend Framework" in technologies:
        return "Backend Application"

    if "Frontend Framework" in technologies:
        return "Frontend Application"

    if languages.get("Python", 0) > 0:
        return "Python Project"

    if languages.get("JavaScript", 0) > 0:
        return "JavaScript Project"

    if languages.get("TypeScript", 0) > 0:
        return "TypeScript Project"

    return "Unknown Project Type"


def get_project_profile(owner: str, repo: str) -> dict:
    """Build a unified profile using one shared GitHub snapshot."""

    github = GitHubClient()

    try:
        # Fetch metadata and Git tree only once.
        snapshot = fetch_repository_snapshot(
            github,
            owner,
            repo,
        )

        # Reuse the same snapshot for both analyses.
        structure = build_repository_structure(
            owner,
            repo,
            snapshot,
        )

        dependency_analysis = build_repository_dependencies(
            github,
            owner,
            repo,
            snapshot,
        )

        languages = structure["language_statistics"]
        technologies = dependency_analysis["technologies"]

        main_dependencies = sorted(
            set(dependency_analysis["requirements"])
            | set(dependency_analysis["pyproject"]["main"])
        )

        development_dependencies = sorted({
            dependency
            for dependencies in dependency_analysis["pyproject"]["optional"].values()
            for dependency in dependencies
        })

        return {
            "repository": structure["repository"],
            "default_branch": structure["default_branch"],
            "project_type": detect_project_type(
                languages,
                technologies,
            ),
            "languages": languages,
            "total_files": structure["total_files"],
            "total_directories": structure["total_directories"],
            "important_files": [
                file["path"]
                for file in structure["important_files"]
            ],
            "dependencies": {
                "main": main_dependencies,
                "development": development_dependencies,
            },
            "technologies": technologies,
            "truncated": (
                structure["truncated"]
                or dependency_analysis["truncated"]
            ),
        }

    finally:
        github.close()
