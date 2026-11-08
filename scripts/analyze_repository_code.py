
from devmate.clients.github_client import GitHubClient
from devmate.tools.repository_tools import fetch_repository_snapshot
from devmate.services.source_code import retrieve_python_source_files
from devmate.services.code_analyzer import analyze_python_file


def main():
    github = GitHubClient()

    try:
        owner = "anushkaSri-04"
        repo = "DevMate-AI"

        snapshot = fetch_repository_snapshot(
            github,
            owner,
            repo,
        )

        source_result = retrieve_python_source_files(
            github,
            owner,
            repo,
            snapshot,
        )

        analyses = [
            analyze_python_file(source_file)
            for source_file in source_result["files"]
        ]

        total_functions = sum(
            len(item["functions"])
            for item in analyses
        )

        total_classes = sum(
            len(item["classes"])
            for item in analyses
        )

        total_imports = sum(
            len(item["imports"])
            for item in analyses
        )

        syntax_errors = [
            item for item in analyses
            if item["syntax_error"] is not None
        ]

        print("\n===== DEV MATE CODE ANALYSIS =====")
        print("Repository:", source_result["repository"])
        print("Files analyzed:", len(analyses))
        print("Functions found:", total_functions)
        print("Classes found:", total_classes)
        print("Imports found:", total_imports)
        print("Syntax errors:", len(syntax_errors))

        print("\n===== FILE-WISE ANALYSIS =====")

        for item in analyses:
            print(f"\nFile: {item['file']}")
            print("Functions:", len(item["functions"]))
            print("Classes:", len(item["classes"]))
            print("Imports:", len(item["imports"]))

            for function in item["functions"]:
                print(
                    f"  Function: {function['name']} "
                    f"(line {function['line']})"
                )

            for cls in item["classes"]:
                print(
                    f"  Class: {cls['name']} "
                    f"(line {cls['line']})"
                )

        if syntax_errors:
            print("\n===== SYNTAX ERRORS =====")

            for item in syntax_errors:
                print(item["file"], item["syntax_error"])

    finally:
        github.close()


if __name__ == "__main__":
    main()
