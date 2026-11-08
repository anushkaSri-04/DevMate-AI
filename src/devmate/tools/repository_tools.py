import base64
import re
import tomllib
from urllib.parse import quote

from devmate.clients.github_client import GitHubClient

IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    ".idea",
    ".vscode",
}


LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
    ".sh": "Shell",
    ".r": "R",
    ".ipynb": "Jupyter Notebook",
}


IMPORTANT_FILES = {
    "README.md": "Project documentation",
    "pyproject.toml": "Python project configuration",
    "requirements.txt": "Python dependencies",
    "Pipfile": "Python dependency management",
    "package.json": "Node.js project configuration",
    "package-lock.json": "Node.js dependency lockfile",
    "Dockerfile": "Docker container configuration",
    "docker-compose.yml": "Docker Compose configuration",
    "compose.yaml": "Docker Compose configuration",
    ".env.example": "Environment variable template",
    "Makefile": "Build and automation commands",
    "setup.py": "Python package configuration",
    "setup.cfg": "Python tool configuration",
    "tsconfig.json": "TypeScript configuration",
    "vite.config.js": "Vite configuration",
    "vite.config.ts": "Vite configuration",
    "pytest.ini": "Pytest configuration",
    ".gitignore": "Git ignore configuration",
}


TECHNOLOGY_CATEGORIES = {
    "fastapi": "Backend Framework",
    "flask": "Backend Framework",
    "django": "Backend Framework",
    "starlette": "Backend Framework",

    "react": "Frontend Framework",
    "next": "Frontend Framework",
    "vue": "Frontend Framework",
    "angular": "Frontend Framework",

    "tensorflow": "Deep Learning",
    "torch": "Deep Learning",
    "keras": "Deep Learning",

    "scikit-learn": "Machine Learning",
    "xgboost": "Machine Learning",
    "lightgbm": "Machine Learning",
    "catboost": "Machine Learning",

    "pandas": "Data Analysis",
    "numpy": "Numerical Computing",
    "matplotlib": "Data Visualization",
    "seaborn": "Data Visualization",
    "plotly": "Data Visualization",

    "langchain": "LLM Framework",
    "llama-index": "LLM Framework",
    "openai": "AI API",
    "transformers": "NLP and Transformers",

    "sqlalchemy": "Database",
    "psycopg2": "Database",
    "pymongo": "Database",

    "pytest": "Testing",
    "ruff": "Code Quality",
    "httpx": "HTTP Client",
    "requests": "HTTP Client",
    "pydantic": "Data Validation",
    "pydantic-settings": "Configuration Management",
    "mcp": "AI Tool Integration",
}




def calculate_language_statistics(
    files: list[dict],
) -> dict[str, int]:
    """Calculate the number of files belonging to each language."""

    language_counts: dict[str, int] = {}

    for file in files:
        extension = file.get("extension")

        language = LANGUAGE_EXTENSIONS.get(extension)

        if language:
            language_counts[language] = (
                language_counts.get(language, 0) + 1
            )

    return dict(
        sorted(
            language_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )


def detect_important_files(files: list[dict]) -> list[dict]:
    """Identify important project and configuration files."""

    important_files = []

    for file in files:
        filename = file["name"]

        if filename in IMPORTANT_FILES:
            important_files.append({
                "path": file["path"],
                "name": filename,
                "purpose": IMPORTANT_FILES[filename],
            })

    return important_files


def fetch_repository_snapshot(
    github: GitHubClient,
    owner: str,
    repo: str,
) -> dict:
    """Fetch repository metadata and its recursive Git tree once."""

    repository_response = github.get(
        f"/repos/{owner}/{repo}"
    )
    repository = repository_response.json()

    default_branch = repository["default_branch"]
    encoded_branch = quote(default_branch, safe="")

    tree_response = github.get(
        f"/repos/{owner}/{repo}/git/trees/"
        f"{encoded_branch}?recursive=1"
    )

    return {
        "repository": f"{owner}/{repo}",
        "default_branch": default_branch,
        "tree_data": tree_response.json(),
    }


def build_repository_structure(
    owner: str,
    repo: str,
    snapshot: dict,
) -> dict:
    """Build repository structure from an existing snapshot."""

    tree_data = snapshot["tree_data"]

    files = []
    directories = set()

    for item in tree_data.get("tree", []):
        path = item["path"]
        path_parts = path.split("/")

        if any(
            part in IGNORED_DIRECTORIES
            for part in path_parts
        ):
            continue

        if item["type"] == "tree":
            directories.add(path)

        elif item["type"] == "blob":
            filename = path_parts[-1]

            files.append({
                "path": path,
                "name": filename,
                "extension": (
                    "." + filename.rsplit(".", 1)[-1]
                    if "." in filename
                    else None
                ),
                "size": item.get("size", 0),
            })

            for index in range(1, len(path_parts)):
                directories.add(
                    "/".join(path_parts[:index])
                )

    return {
        "repository": snapshot["repository"],
        "default_branch": snapshot["default_branch"],
        "total_files": len(files),
        "total_directories": len(directories),
        "files": files,
        "directories": sorted(directories),
        "truncated": tree_data.get("truncated", False),
        "language_statistics": calculate_language_statistics(files),
        "important_files": detect_important_files(files),
    }



def analyze_repository_structure(
    owner: str,
    repo: str,
) -> dict:
    """Retrieve and analyze a GitHub repository's structure."""
    github = GitHubClient()
    try:
        snapshot = fetch_repository_snapshot(
            github,
            owner,
            repo,
        )
        return build_repository_structure(
            owner,
            repo,
            snapshot,
        )
    finally:
        github.close()



def get_repository_file_content(
    github: GitHubClient,
    owner: str,
    repo: str,
    path: str,
) -> str:
    """Retrieve and decode a text file from GitHub."""

    response = github.get(
        f"/repos/{owner}/{repo}/contents/{path}"
    )

    file_data = response.json()

    if file_data.get("encoding") != "base64":
        raise ValueError(
            f"Unsupported file encoding for {path}"
        )

    encoded_content = file_data["content"]

    decoded_content = base64.b64decode(
        encoded_content
    ).decode("utf-8")

    return decoded_content


def build_repository_dependencies(
    github: GitHubClient,
    owner: str,
    repo: str,
    snapshot: dict,
) -> dict:
    """Analyze dependencies using an existing repository snapshot."""

    tree_data = snapshot["tree_data"]

    dependency_paths = {
        item["path"]
        for item in tree_data.get("tree", [])
        if item["type"] == "blob"
        and item["path"] in {
            "requirements.txt",
            "pyproject.toml",
        }
    }

    result = {
        "repository": snapshot["repository"],
        "requirements": [],
        "pyproject": {
            "main": [],
            "optional": {},
        },
        "files_analyzed": [],
        "truncated": tree_data.get("truncated", False),
    }

    if "requirements.txt" in dependency_paths:
        content = get_repository_file_content(
            github,
            owner,
            repo,
            "requirements.txt",
        )

        result["requirements"] = parse_requirements(content)
        result["files_analyzed"].append("requirements.txt")

    if "pyproject.toml" in dependency_paths:
        content = get_repository_file_content(
            github,
            owner,
            repo,
            "pyproject.toml",
        )

        result["pyproject"] = parse_pyproject_dependencies(
            content
        )
        result["files_analyzed"].append("pyproject.toml")

    all_dependencies = set(result["requirements"])
    all_dependencies.update(result["pyproject"]["main"])

    for dependencies in result["pyproject"]["optional"].values():
        all_dependencies.update(dependencies)

    result["technologies"] = detect_technologies(
        sorted(all_dependencies)
    )

    return result



def analyze_repository_dependencies(
    owner: str,
    repo: str,
) -> dict:
    """Analyze dependencies declared in GitHub repository files."""
    github = GitHubClient()
    try:
        snapshot = fetch_repository_snapshot(
            github,
            owner,
            repo,
        )
        return build_repository_dependencies(
            github,
            owner,
            repo,
            snapshot,
        )
    finally:
        github.close()



def parse_requirements(content: str) -> list[str]:
    """Extract dependency names from requirements.txt."""

    dependencies = []

    for line in content.splitlines():
        line = line.strip()

        # Ignore comments, empty lines and pip options.
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Remove inline comments.
        line = line.split(" #", 1)[0].strip()

        match = re.match(
            r"^([A-Za-z0-9][A-Za-z0-9._-]*)",
            line,
        )

        if match:
            dependencies.append(match.group(1).lower())

    return sorted(set(dependencies))


def parse_pyproject_dependencies(content: str) -> dict:
    """Extract dependencies declared in pyproject.toml."""

    config = tomllib.loads(content)

    project = config.get("project", {})

    main_dependencies = project.get("dependencies", [])

    optional_dependencies = project.get(
        "optional-dependencies",
        {},
    )

    return {
        "main": sorted({
            re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", dep)
            .group(1).lower()
            for dep in main_dependencies
            if re.match(
                r"^([A-Za-z0-9][A-Za-z0-9._-]*)",
                dep,
            )
        }),
        "optional": {
            group: sorted({
                match.group(1).lower()
                for dep in dependencies
                if (
                    match := re.match(
                        r"^([A-Za-z0-9][A-Za-z0-9._-]*)",
                        dep,
                    )
                )
            })
            for group, dependencies in optional_dependencies.items()
        },
    }



def detect_technologies(dependencies: list[str]) -> dict:
    """Identify technologies based on declared dependencies."""

    technologies = {}

    for dependency in dependencies:
        category = TECHNOLOGY_CATEGORIES.get(
            dependency.lower()
        )

        if category:
            technologies.setdefault(category, []).append(
                dependency
            )

    return {
        category: sorted(set(packages))
        for category, packages in sorted(
            technologies.items()
        )
    }

