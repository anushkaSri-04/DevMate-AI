
"""Retrieve Python source files from a GitHub repository."""

from devmate.tools.repository_tools import (
    IGNORED_DIRECTORIES,
    get_repository_file_content,
)


MAX_PYTHON_FILES = 50
MAX_FILE_SIZE_BYTES = 100_000


def retrieve_python_source_files(
    github,
    owner: str,
    repo: str,
    snapshot: dict,
) -> dict:
    """Retrieve Python source files using an existing repository snapshot."""

    tree_data = snapshot["tree_data"]

    python_files = []

    for item in tree_data.get("tree", []):
        path = item["path"]

        if item["type"] != "blob":
            continue

        if not path.endswith(".py"):
            continue

        path_parts = path.split("/")

        if any(
            part in IGNORED_DIRECTORIES
            for part in path_parts
        ):
            continue

        file_size = item.get("size", 0)

        if file_size > MAX_FILE_SIZE_BYTES:
            continue

        python_files.append({
            "path": path,
            "size": file_size,
        })

    python_files = sorted(
        python_files,
        key=lambda item: item["path"],
    )[:MAX_PYTHON_FILES]

    retrieved_files = []
    failed_files = []

    for file in python_files:
        path = file["path"]

        try:
            content = get_repository_file_content(
                github,
                owner,
                repo,
                path,
            )

            retrieved_files.append({
                "path": path,
                "content": content,
                "line_count": len(content.splitlines()),
                "size": file["size"],
            })

        except Exception as error:
            failed_files.append({
                "path": path,
                "error": str(error),
            })

    return {
        "repository": snapshot["repository"],
        "total_python_files_found": len(python_files),
        "total_files_analyzed": len(retrieved_files),
        "files": retrieved_files,
        "failed_files": failed_files,
        "truncated": tree_data.get("truncated", False),
    }
