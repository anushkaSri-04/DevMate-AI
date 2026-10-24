import httpx
import respx

from tools.github_client import GitHubClient


@respx.mock
def test_github_client_retries_after_429():
    route = respx.get(
        "https://api.github.com/user"
    ).mock(
        side_effect=[
            httpx.Response(
                429,
                headers={
                    "Retry-After": "0",
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "0",
                },
            ),
            httpx.Response(
                200,
                json={
                    "login": "anushkaSri-04",
                },
                headers={
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "4999",
                },
            ),
        ]
    )

    github = GitHubClient()

    try:
        response = github.get("/user")

        assert response.status_code == 200
        assert response.json()["login"] == "anushkaSri-04"
        assert route.call_count == 2

    finally:
        github.close()