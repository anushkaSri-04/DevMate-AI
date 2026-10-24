from tools.github_tools import get_repository_details


repository = get_repository_details(
    "anushkaSri-04",
    "Behavior-Based-Alternative-Credit-Scoring",
)

print("Repository:", repository["full_name"])
print("Description:", repository["description"])
print("Private:", repository["private"])
print("Default branch:", repository["default_branch"])
print("Language:", repository["language"])