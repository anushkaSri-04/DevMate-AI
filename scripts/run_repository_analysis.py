
from devmate.clients.github_client import GitHubClient
from devmate.tools.repository_tools import fetch_repository_snapshot
from devmate.services.repository_code_analysis import (
    analyze_repository_code,
)


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

        result = analyze_repository_code(
            github,
            owner,
            repo,
            snapshot,
        )

        # ==================================================
        # REPOSITORY HEADER
        # ==================================================

        print("\n===== DEV MATE REPOSITORY INTELLIGENCE =====")
        print("Repository:", result["repository"])

        # ==================================================
        # REPOSITORY SUMMARY
        # ==================================================

        print("\n===== SUMMARY =====")

        for key, value in result["summary"].items():
            print(f"{key}: {value}")

        # ==================================================
        # FILE ANALYSIS
        # ==================================================

        print("\n===== FILE ANALYSIS =====")

        for file_data in result["files"]:

            print(f"\nFile: {file_data['file']}")

            for function in file_data["functions"]:
                print(
                    f"  Function: {function['name']} "
                    f"(line {function['line']})"
                )

            for cls in file_data["classes"]:
                print(
                    f"  Class: {cls['name']} "
                    f"(line {cls['line']})"
                )

                for method in cls["methods"]:
                    print(
                        f"    Method: {method['name']} "
                        f"(line {method['line']})"
                    )

            # Entry-point detection
            entry_point = file_data.get("entry_point", {})

            if entry_point.get("is_entry_point"):
                print("  Entry Point: Yes")

                for guard in entry_point.get("main_guards", []):
                    print(
                        f"  Main Guard: line {guard['line']}"
                    )

                    print(
                        f"  Calls main(): {guard['calls_main']}"
                    )

                    for call in guard["calls"]:
                        print(
                            f"    Call: {call['name']} "
                            f"(line {call['line']})"
                        )

        # ==================================================
        # MODULE RELATIONSHIPS
        # ==================================================

        relationships = result["module_relationships"]

        print("\n===== MODULE RELATIONSHIPS =====")

        # Module Index
        print("\n--- Module Index ---")

        for module, path in relationships["module_index"].items():
            print(f"{module} -> {path}")

        # Internal Dependencies
        print("\n--- Internal Dependencies ---")

        for dependency in relationships["dependencies"]:
            print(
                f"{dependency['source']} "
                f"-> {dependency['target']} "
                f"(line {dependency['line']})"
            )

        # External Imports
        print("\n--- External Imports ---")

        for item in relationships["external_imports"]:
            print(
                f"{item['file']} -> {item['module']} "
                f"(line {item['line']})"
            )

        # Unresolved Imports
        print("\n--- Unresolved Imports ---")

        for item in relationships["unresolved_imports"]:
            print(
                f"{item['file']} -> {item['import']}"
            )

        # ==================================================
        # MODULE RELATIONSHIP SUMMARY
        # ==================================================

        print("\n--- Relationship Summary ---")

        print(
            "Total modules:",
            relationships["total_modules"],
        )

        print(
            "Internal dependencies:",
            relationships["total_internal_dependencies"],
        )

        print(
            "External imports:",
            relationships["total_external_imports"],
        )

        print(
            "Unresolved imports:",
            relationships["total_unresolved_imports"],
        )

        
        # ==================================================
        # REPOSITORY ENTRY-POINT ANALYSIS
        # ==================================================

        entry_analysis = result["entry_point_analysis"]

        print("\n===== REPOSITORY ENTRY-POINT ANALYSIS =====")

        print(
            "Confirmed entry points:",
            entry_analysis["total_confirmed_entry_points"],
        )

        print(
            "Entry-point candidates:",
            entry_analysis["total_entry_point_candidates"],
        )

        print("\n--- Classification Summary ---")

        for classification, count in entry_analysis[
            "classification_counts"
        ].items():
            print(f"{classification}: {count}")

        print("\n--- Confirmed Entry Points ---")

        for item in entry_analysis["entry_points"]:
            print(f"\nFile: {item['file']}")
            print(f"Classification: {item['classification']}")

            for evidence in item["evidence"]:
                print("  Evidence:", evidence)

        print("\n--- Entry-Point Candidates ---")

        for item in entry_analysis["candidates"]:
            print(f"\nFile: {item['file']}")
            print(f"Classification: {item['classification']}")

            for evidence in item["evidence"]:
                print("  Evidence:", evidence)

        print("\n--- Pyproject Console Scripts ---")

        if entry_analysis["pyproject_found"]:
            if entry_analysis["project_scripts"]:
                for script in entry_analysis["project_scripts"]:
                    print(f"{script['name']} -> {script['target']}")
                    print(f"  Resolved file: {script['file']}")
            else:
                print("No console scripts configured.")

            if entry_analysis["configuration_error"]:
                print(
                    "Configuration error:",
                    entry_analysis["configuration_error"],
                )
        else:
            print("pyproject.toml not found.")



        # ==================================================
        # SYNTAX ERRORS
        # ==================================================

        if result["syntax_errors"]:
            print("\n===== SYNTAX ERRORS =====")

            for error in result["syntax_errors"]:
                print(error)

        else:
            print("\n===== SYNTAX ERRORS =====")
            print("No syntax errors detected.")

        # ==================================================
        # FAILED FILES
        # ==================================================

        if result["failed_files"]:
            print("\n===== FAILED FILES =====")

            for failed_file in result["failed_files"]:
                print(failed_file)

        else:
            print("\n===== FAILED FILES =====")
            print("No failed files.")

        # ==================================================
        # ANALYSIS STATUS
        # ==================================================

        print("\n===== ANALYSIS STATUS =====")

        print(
            "Files analyzed:",
            result["summary"]["total_files_analyzed"],
        )

        print(
            "Module relationships analyzed:",
            relationships["total_internal_dependencies"],
        )

        # ==================================================
        # CROSS-FILE CODE UNDERSTANDING
        # ==================================================

        cross_file = result["cross_file_analysis"]

        print("\n===== CROSS-FILE CODE UNDERSTANDING =====")

        print("\n--- Symbol Summary ---")
        print("Total symbols:", cross_file["total_symbols"])
        print("Unique symbol names:", cross_file["total_symbol_names"])
        print("Resolved references:", cross_file["total_references"])
        print(
            "Unresolved references:",
            cross_file["total_unresolved_references"],
        )

        print("\n--- Symbol Definitions ---")

        for definition in cross_file["definitions"]:
            print(
                f"{definition['type']}: {definition['name']} "
                f"-> {definition['file']} "
                f"(line {definition['line']})"
            )

        print("\n--- Imported By ---")

        for item in cross_file["imported_by"]:
            print(
                f"\n{item['symbol']} defined in {item['target_file']}"
            )

            for reference in item["references"]:
                print(
                    f"  Imported by: {reference['file']} "
                    f"(line {reference['line']})"
                )

        print("\n--- Resolved Function References ---")

        if cross_file["references"]:
            print(
                "DEBUG reference keys:",
                cross_file["references"][0].keys()
            )

            for reference in cross_file["references"]:
                symbol = (
                    reference.get("symbol")
                    or reference.get("name")
                    or "<unknown>"
                )

                source_file = reference.get("source_file", "<unknown>")
                call_line = reference.get("call_line", "?")
                target_file = reference.get("target_file", "<unknown>")
                definition_line = reference.get("definition_line", "?")

            print(
                f"{source_file}:{call_line} "
                f"-> {symbol} "
                f"-> {target_file}:{definition_line}"
            )
        else:
            print("No resolved cross-file references found.")


        print("\n--- Unresolved References ---")

        if cross_file["unresolved_references"]:
            for reference in cross_file["unresolved_references"]:
                print(reference)
        else:
            print("No unresolved references found.")

        # ==================================================
        # ENTRY POINT FILES
        # ==================================================

        print(
            "Entry-point files:",
            sum(
                1
                for file_data in result["files"]
                if file_data.get("entry_point", {}).get(
                    "is_entry_point",
                    False,
                )
            ),
        )

        print("\n===== ANALYSIS COMPLETE =====")

    finally:
        github.close()


if __name__ == "__main__":
    main()
