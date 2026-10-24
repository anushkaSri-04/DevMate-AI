from config import settings


print("GitHub API:", settings.github_api_base_url)
print("Token loaded:", bool(settings.github_token))