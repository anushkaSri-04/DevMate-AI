
import tomllib
from pathlib import PurePosixPath

from devmate.tools.repository_tools import get_repository_file_content


CONVENTIONAL_ENTRY_FILES = {
    "main.py": "conventional_filename",
    "app.py": "conventional_filename",
    "run.py": "conventional_filename",
    "__main__.py": "python_module_entry_point",
}


def get_module_name(path: str) -> str:
    """Convert a Python file path into a likely importable module name."""

    file_path = PurePosixPath(path)

    if file_path.name == "__init__.py":
        parts = list(file_path.parent.parts)
    else:
        parts = list(file_path.with_suffix("").parts)

    if parts and parts[0] == "src":
        parts = parts[1:]

    return ".".join(parts)


def find_script_file(
    module_name: str,
    file_analyses: list[dict],
) -> str | None:
    """Find the repository file corresponding to a console-script module."""

    normalized_module = module_name.removesuffix(".__main__")

    for file_data in file_analyses:
        if get_module_name(file_data["file"]) == normalized_module:
            return file_data["file"]

    return None


def analyze_pyproject_scripts(
    github,
    owner: str,
    repo: str,
    snapshot: dict,
    file_analyses: list[dict],
) -> dict:
    """Read console-script declarations from pyproject.toml."""

    tree_items = snapshot["tree_data"].get("tree", [])

    pyproject_exists = any(
        item.get("type") == "blob"
        and item.get("path") == "pyproject.toml"
        for item in tree_items
    )

    if not pyproject_exists:
        return {
            "found": False,
            "scripts": [],
            "error": None,
        }

    try:
        content = get_repository_file_content(
            github,
            owner,
            repo,
            "pyproject.toml",
        )
        config = tomllib.loads(content)

    except Exception as error:
        return {
            "found": True,
            "scripts": [],
            "error": str(error),
        }

    project_scripts = config.get(
        "project", {}
    ).get("scripts", {})

    scripts = []

    for script_name, target in project_scripts.items():
        target = str(target)
        module_name, separator, function_name = target.partition(":")

        module_name = module_name.strip()
        function_name = function_name.strip() if separator else None

        scripts.append({
            "name": script_name,
            "target": target,
            "module": module_name,
            "function": function_name,
            "file": find_script_file(
                module_name,
                file_analyses,
            ),
        })

    return {
        "found": True,
        "scripts": scripts,
        "error": None,
    }


def classify_entry_point(
    path: str,
    evidence: list[dict],
) -> str:
    """Classify an entry point using its available evidence."""

    filename = PurePosixPath(path).name

    evidence_types = {
        item["type"]
        for item in evidence
    }

    # Explicit console-script configuration has strong evidence.
    if "project_script" in evidence_types:
        return "configured_console_script"

    # __main__.py is executable through python -m.
    if filename == "__main__.py":
        return "module_entry_point"

    main_guard_evidence = [
        item
        for item in evidence
        if item["type"] == "main_guard"
    ]

    if main_guard_evidence:
        # main.py is the primary application when it has a main guard.
        if filename == "main.py":
            return "primary_application"

        # A guard calling main() is strong application-startup evidence.
        if any(
            item["calls_main"]
            for item in main_guard_evidence
        ):
            return "primary_application"

        # Other guarded files are standalone executable utilities.
        return "standalone_utility"

    return "candidate"


def analyze_repository_entry_points(
    github,
    owner: str,
    repo: str,
    snapshot: dict,
    file_analyses: list[dict],
) -> dict:
    """Detect and classify repository entry points."""

    entry_points = {}

    for file_data in file_analyses:
        path = file_data["file"]
        filename = PurePosixPath(path).name

        evidence = []

        # Evidence 1: Explicit Python main guard.
        ast_entry_point = file_data.get("entry_point", {})

        if ast_entry_point.get("is_entry_point"):
            for guard in ast_entry_point.get("main_guards", []):
                evidence.append({
                    "type": "main_guard",
                    "line": guard["line"],
                    "calls_main": guard["calls_main"],
                })

        # Evidence 2: Conventional filenames.
        if filename in CONVENTIONAL_ENTRY_FILES:
            evidence.append({
                "type": CONVENTIONAL_ENTRY_FILES[filename],
                "filename": filename,
            })

        if evidence:
            entry_points[path] = {
                "file": path,
                "evidence": evidence,
            }

    # Evidence 3: Console scripts configured in pyproject.toml.
    project_scripts = analyze_pyproject_scripts(
        github,
        owner,
        repo,
        snapshot,
        file_analyses,
    )

    for script in project_scripts["scripts"]:
        path = script["file"]

        if not path:
            continue

        entry_point = entry_points.setdefault(
            path,
            {
                "file": path,
                "evidence": [],
            },
        )

        entry_point["evidence"].append({
            "type": "project_script",
            "script_name": script["name"],
            "target": script["target"],
        })

    # Assign classifications.
    results = []

    for item in entry_points.values():
        classification = classify_entry_point(
            item["file"],
            item["evidence"],
        )

        results.append({
            **item,
            "classification": classification,
            "is_confirmed": classification != "candidate",
            "is_candidate": classification == "candidate",
        })

    confirmed = [
        item for item in results
        if item["is_confirmed"]
    ]

    candidates = [
        item for item in results
        if item["is_candidate"]
    ]

    classification_counts = {}

    for item in results:
        classification = item["classification"]
        classification_counts[classification] = (
            classification_counts.get(classification, 0) + 1
        )

    return {
        "total_confirmed_entry_points": len(confirmed),
        "total_entry_point_candidates": len(candidates),
        "classification_counts": classification_counts,
        "entry_points": confirmed,
        "candidates": candidates,
        "project_scripts": project_scripts["scripts"],
        "pyproject_found": project_scripts["found"],
        "configuration_error": project_scripts["error"],
    }
