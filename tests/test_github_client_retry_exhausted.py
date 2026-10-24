import httpx
import pytest
import respx

from tools.github_client import GitHubClient


@respx.mock
def test_github_client_fails_after_max_retries():
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
                429,
                headers={
                    "Retry-After": "0",
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "0",
                },
            ),
            httpx.Response(
                429,
                headers={
                    "Retry-After": "0",
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "0",
                },
            ),
            httpx.Response(
                429,
                headers={
                    "Retry-After": "0",
                    "X-RateLimit-Limit": "5000",
                    "X-RateLimit-Remaining": "0",
                },
            ),
        ]
    )

    github = GitHubClient()

    try:
        with pytest.raises(httpx.HTTPStatusError):
            github.get("/user")

        assert route.call_count == 4

    finally:
        github.close()