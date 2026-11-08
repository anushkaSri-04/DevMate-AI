
from devmate.services.source_code import (
    retrieve_python_source_files,
)
from devmate.services.code_analyzer import (
    analyze_python_file,
)
from devmate.services.module_graph import (
    analyze_module_relationships,
)
from devmate.services.entry_point_analysis import (
    analyze_repository_entry_points,
)
from devmate.clients.github_client import GitHubClient
from devmate.tools.repository_tools import fetch_repository_snapshot
from devmate.services.cross_file_analysis import (
    analyze_cross_file_references,
)


def analyze_repository_code(
    github,
    owner: str,
    repo: str,
    snapshot: dict,
) -> dict:
    """Retrieve and analyze Python source code across a repository."""

    # Step 1: Retrieve Python source files.
    source_result = retrieve_python_source_files(
        github,
        owner,
        repo,
        snapshot,
    )

    # Step 2: Analyze each retrieved Python file.
    file_analyses = [
        analyze_python_file(source_file)
        for source_file in source_result["files"]
    ]

    # Step 3: Analyze relationships between Python modules.
    module_relationships = analyze_module_relationships(
        file_analyses
    )
    # Step 4: Analyze cross-file symbols and references.
    cross_file_analysis = analyze_cross_file_references(
        file_analyses,
        module_relationships,
    )
    print("\n===== CROSS-FILE DEBUG =====")
    print("Definitions:", len(cross_file_analysis.get("definitions", [])))
    print("Imported by:", len(cross_file_analysis.get("imported_by", [])))
    print("Resolved:", len(cross_file_analysis.get("references", [])))
    print(
        "Unresolved:",
        len(cross_file_analysis.get("unresolved_references", []))
    )
    print("Result keys:", list(cross_file_analysis.keys()))
    print("\n===== FUNCTION CALL DEBUG =====")

    for item in file_analyses:
        calls = item.get("function_calls", [])

        if calls:
            print(f"\nFile: {item['file']}")
            print(f"Total calls: {len(calls)}")

            for call in calls[:10]:
                print(call)

    print(
        "\nTotal function calls:",
        sum(len(item.get("function_calls", [])) for item in file_analyses)
    )

    # Step 4: Detect repository entry points.
    entry_point_analysis = analyze_repository_entry_points(
        github,
        owner,
        repo,
        snapshot,
        file_analyses,
    )

    # Step 5: Calculate repository-wide statistics.
    total_functions = sum(
        len(item["functions"])
        for item in file_analyses
    )

    total_classes = sum(
        len(item["classes"])
        for item in file_analyses
    )

    total_methods = sum(
        len(cls["methods"])
        for item in file_analyses
        for cls in item["classes"]
    )

    total_imports = sum(
        len(item["imports"])
        for item in file_analyses
    )

    total_function_calls = sum(
        len(item["function_calls"])
        for item in file_analyses
    )

    syntax_errors = [
        {
            "file": item["file"],
            **item["syntax_error"],
        }
        for item in file_analyses
        if item["syntax_error"] is not None
    ]

    # Step 6: Build the final repository analysis.
    return {
        "repository": source_result["repository"],
        "source_files": source_result["files"],

        "summary": {
            "total_python_files_found": (
                source_result["total_python_files_found"]
            ),
            "total_files_analyzed": len(file_analyses),
            "total_functions": total_functions,
            "total_classes": total_classes,
            "total_methods": total_methods,
            "total_imports": total_imports,
            "total_function_calls": total_function_calls,
            "total_syntax_errors": len(syntax_errors),
            "total_confirmed_entry_points": (
                entry_point_analysis[
                    "total_confirmed_entry_points"
                ]
            ),
            "total_entry_point_candidates": (
                entry_point_analysis[
                    "total_entry_point_candidates"
                ]
            ),
            "total_symbols": cross_file_analysis["total_symbols"],
            "total_resolved_references": cross_file_analysis["total_references"],
            "total_unresolved_references": (
                cross_file_analysis["total_unresolved_references"]
            ),
        },

        "files": file_analyses,
        "entry_point_analysis": entry_point_analysis,
        "syntax_errors": syntax_errors,
        "failed_files": source_result["failed_files"],
        "truncated": source_result["truncated"],
        "module_relationships": module_relationships,
        "cross_file_analysis": cross_file_analysis,
    }


def get_repository_code_analysis(
    owner: str,
    repo: str,
) -> dict:
    """Retrieve and analyze Python source code in a GitHub repository."""

    github = GitHubClient()

    try:
        snapshot = fetch_repository_snapshot(
            github,
            owner,
            repo,
        )

        return analyze_repository_code(
            github,
            owner,
            repo,
            snapshot,
        )

    finally:
        github.close()
