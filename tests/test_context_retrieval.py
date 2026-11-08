
from devmate.clients.github_client import GitHubClient

from devmate.tools.repository_tools import (
    fetch_repository_snapshot,
)

from devmate.services.source_code import (
    retrieve_python_source_files,
)

from devmate.services.repository_code_analysis import (
    analyze_repository_code,
)

from devmate.services.context_retrieval import (
    retrieve_symbol_context,
    retrieve_reference_context,
    retrieve_import_context,
    retrieve_related_file_context,
    retrieve_query_context,
    build_context_package,
)


OWNER = "anushkaSri-04"
REPO = "DevMate-AI"


def main():
    github = GitHubClient()

    try:
        snapshot = fetch_repository_snapshot(
            github,
            OWNER,
            REPO,
        )

        source_result = retrieve_python_source_files(
            github,
            OWNER,
            REPO,
            snapshot,
        )

        analysis = analyze_repository_code(
            github,
            OWNER,
            REPO,
            snapshot,
        )

        source_files = source_result["files"]

        print("\n===== SYMBOL CONTEXT =====")

        print(
            retrieve_symbol_context(
                analysis,
                source_files,
                "list_issues",
            )
        )

        print("\n===== REFERENCE CONTEXT =====")

        print(
            retrieve_reference_context(
                analysis,
                source_files,
                "list_issues",
            )
        )

        print("\n===== IMPORT CONTEXT =====")

        print(
            retrieve_import_context(
                analysis,
                source_files,
                "GitHubClient",
            )
        )

        print("\n===== RELATED FILE CONTEXT =====")

        print(
            retrieve_related_file_context(
                analysis,
                source_files,
                "tools/github_tools.py",
            )
        )

        print("\n===== NATURAL LANGUAGE CONTEXT =====")

        result = retrieve_query_context(
            analysis,
            source_files,
            "How does DevMate retrieve GitHub issues?",
        )

        print("Total contexts:", result["total_contexts"])
        print("Search terms:", result["search_terms"])

        for context in result["contexts"]:
            print("\nFile:", context["file"])
            print("Type:", context["type"])
            print("Lines:", context["start_line"], "-", context["end_line"])
            print(context["snippet"])

        print("\n===== FINAL CONTEXT PACKAGE =====")

        package = build_context_package(
            analysis,
            source_files,
            "How does DevMate retrieve GitHub issues?",
        )

        print(package)

    finally:
        github.close()


if __name__ == "__main__":
    main()
