from tools.github_tools import count_open_issues_across_repositories


repositories = [
    ("anushkaSri-04", "AI_Resume_Analyzer"),
    ("anushkaSri-04", "Behavior-Based-Alternative-Credit-Scoring"),
]

result = count_open_issues_across_repositories(repositories)

for repository in result["repositories"]:
    print(
        repository["repository"],
        "→",
        repository["open_issue_count"],
    )

print("Total open issues:", result["total_open_issues"])