from tools.github_client import GitHubClient


github = GitHubClient()

try:
    response = github.get("/user")

    user = response.json()

    print("Authenticated successfully!")
    print("GitHub username:", user["login"])

finally:
    github.close()