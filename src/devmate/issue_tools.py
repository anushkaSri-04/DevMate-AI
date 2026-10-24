"""Issue-related functions for DevMate AI."""


def count_open_issues(
    total_issues: int,
    closed_issues: int
) -> int:
    """Return the number of open issues."""

    if total_issues < 0 or closed_issues < 0:
        raise ValueError("Issue counts cannot be negative.")

    if closed_issues > total_issues:
        raise ValueError(
            "Closed issues cannot exceed total issues."
        )

    return total_issues - closed_issues


def count_closed_issues(
    total_issues: int,
    open_issues: int
) -> int:
    """Return the number of closed issues."""

    if total_issues < 0 or open_issues < 0:
        raise ValueError("Issue counts cannot be negative.")

    if open_issues > total_issues:
        raise ValueError(
            "Open issues cannot exceed total issues."
        )

    return total_issues - open_issues