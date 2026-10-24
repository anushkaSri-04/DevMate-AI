from tools.github_client import GitHubClient


def list_repositories() -> list[dict]:
    """Return repositories belonging to the authenticated GitHub user."""
    github = GitHubClient()

    try:
        response = github.get("/user/repos")
        return response.json()
    finally:
        github.close()

def get_repository_details(owner: str, repo: str) -> dict:
    """Return details for a specific GitHub repository."""
    github = GitHubClient()

    try:
        response = github.get(f"/repos/{owner}/{repo}")
        return response.json()
    finally:
        github.close()

def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 30,
    max_pages: int = 5,
) -> tuple[list[dict], bool]:
    """Return actual GitHub issues and whether all pages were retrieved."""
    if state not in {"open", "closed", "all"}:
        raise ValueError("state must be 'open', 'closed', or 'all'")
    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100")
    if not 1 <= max_pages <= 10:
        raise ValueError("max_pages must be between 1 and 10")
    github = GitHubClient()
    issues: list[dict] = []
    try:
        for page in range(1, max_pages + 1):
            response = github.get(
                f"/repos/{owner}/{repo}/issues"
                f"?state={state}"
                f"&per_page={per_page}"
                f"&page={page}"
            )
            page_items = response.json()
            if not page_items:
                return issues, True
            for item in page_items:
                if "pull_request" not in item:
                    issues.append(item)
            if len(page_items) < per_page:
                return issues, True
        return issues, False
    finally:
        github.close()

def count_open_issues(
    owner: str,
    repo: str,
) -> dict:
    """Return the open issue count and pagination status."""
    issues, complete = list_issues(
        owner=owner,
        repo=repo,
        state="open",
    )
    return {
        "owner": owner,
        "repository": repo,
        "open_issue_count": len(issues),
        "complete": complete,
    }

def count_open_issues_across_repositories(
    repositories: list[tuple[str, str]],
) -> dict:
    """Count open issues across multiple repositories."""
    results = []
    total = 0
    for owner, repo in repositories:
        result = count_open_issues(owner, repo)
        results.append(result)
        total += result["open_issue_count"]
    return {
        "repositories": results,
        "total_open_issues": total,
    }



if __name__ == "__main__":
    repositories = list_repositories()
    print(f"Found {len(repositories)} repositories:")
    for repo in repositories:
        print(f"- {repo['full_name']}")

    