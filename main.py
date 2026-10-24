"""Entry point for MCP DevMate AI."""

from src.devmate.issue_tools import (
    count_open_issues,
    count_closed_issues,
)


def main() -> None:
    total_issues = 20
    closed_issues = 7

    open_issues = count_open_issues(
        total_issues,
        closed_issues
    )

    print(f"Total issues: {total_issues}")
    print(f"Open issues: {open_issues}")
    print(
        f"Closed issues: "
        f"{count_closed_issues(total_issues, open_issues)}"
    )


if __name__ == "__main__":
    main()