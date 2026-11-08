from devmate.tools.github_tools import list_issues

issues, complete = list_issues(
    "anushkaSri-04",
    "Behavior-Based-Alternative-Credit-Scoring",
)

print(f"Found {len(issues)} issues")
print(f"Retrieval complete: {complete}")

for issue in issues:
    print(
        f"#{issue['number']} - "
        f"{issue['title']}"
    )