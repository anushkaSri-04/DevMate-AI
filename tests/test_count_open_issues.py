from tools.github_tools import count_open_issues


result = count_open_issues(
    "anushkaSri-04",
    "AI_Resume_Analyzer",
)

print("Repository:", result["repository"])
print("Open issues:", result["open_issue_count"])
print("Complete:", result["complete"])