
from devmate.tools.github_tools import (
    count_open_issues,
    get_repository_details,
    list_issues,
    list_repositories,
)

OWNER = "anushkaSri-04"
REPO = "Behavior-Based-Alternative-Credit-Scoring"


def main():
    results = {}

    print("=" * 55)
    print("DEVMATE AI - LIVE GITHUB TESTING")
    print("=" * 55)

    # TEST 1: List repositories
    print("\n[TEST 1] LIST REPOSITORIES")

    try:
        repositories = list_repositories()

        assert isinstance(repositories, list)

        print("Repositories found:", len(repositories))

        for repository in repositories:
            print("-", repository["full_name"])

        results["list_repositories"] = "PASSED"

    except Exception as error:
        print("FAILED:", error)
        results["list_repositories"] = "FAILED"

    # TEST 2: Get repository details
    print("\n[TEST 2] GET REPOSITORY DETAILS")

    try:
        details = get_repository_details(OWNER, REPO)

        assert details["full_name"].lower() == f"{OWNER}/{REPO}".lower()

        print("Name:", details["name"])
        print("Full name:", details["full_name"])
        print("Private:", details["private"])
        print("Default branch:", details["default_branch"])

        results["get_repository_details"] = "PASSED"

    except Exception as error:
        print("FAILED:", error)
        results["get_repository_details"] = "FAILED"

    # TEST 3: List issues
    print("\n[TEST 3] LIST ISSUES")

    try:
        issues, complete = list_issues(
            OWNER,
            REPO,
            state="open",
            per_page=30,
            max_pages=5,
        )

        assert isinstance(issues, list)
        assert isinstance(complete, bool)

        print("Issues found:", len(issues))
        print("Retrieval complete:", complete)

        for issue in issues:
            print(f"#{issue['number']} - {issue['title']}")

        results["list_issues"] = "PASSED"

    except Exception as error:
        print("FAILED:", error)
        results["list_issues"] = "FAILED"

    # TEST 4: Count open issues
    print("\n[TEST 4] COUNT OPEN ISSUES")

    try:
        result = count_open_issues(OWNER, REPO)

        assert isinstance(result["open_issue_count"], int)
        assert result["open_issue_count"] >= 0

        print("Open issues:", result["open_issue_count"])
        print("Retrieval complete:", result["complete"])

        results["count_open_issues"] = "PASSED"

    except Exception as error:
        print("FAILED:", error)
        results["count_open_issues"] = "FAILED"

    # FINAL REPORT
    print("\n" + "=" * 55)
    print("FINAL TEST REPORT")
    print("=" * 55)

    for function, status in results.items():
        print(f"{function}: {status}")

    passed = sum(status == "PASSED" for status in results.values())
    failed = len(results) - passed

    print("\nTotal:", len(results))
    print("Passed:", passed)
    print("Failed:", failed)

    print(
        "\nRESULT:",
        "ALL TESTS PASSED" if failed == 0 else "SOME TESTS FAILED",
    )


if __name__ == "__main__":
    main()
