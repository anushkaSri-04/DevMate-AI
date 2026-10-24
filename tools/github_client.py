import time
from datetime import datetime, timezone

import httpx

from tools.config import settings


class GitHubClient:
    """Client for communicating with the GitHub REST API."""

    def __init__(self) -> None:
        self.client = httpx.Client(
            base_url=settings.github_api_base_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {settings.github_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10.0,
        )

    def _get_retry_delay(
        self,
        response: httpx.Response,
        attempt: int,
    ) -> float:
        """Calculate how long to wait before retrying a request."""

        retry_after = response.headers.get("Retry-After")

        if retry_after is not None:
            try:
                return float(retry_after)
            except ValueError:
                pass

        reset_timestamp = response.headers.get("X-RateLimit-Reset")

        if reset_timestamp is not None:
            try:
                reset_time = datetime.fromtimestamp(
                    int(reset_timestamp),
                    tz=timezone.utc,
                )

                now = datetime.now(timezone.utc)

                delay = (reset_time - now).total_seconds()

                if delay > 0:
                    return delay

            except (ValueError, OverflowError):
                pass

        return float(2**attempt)

    def get(self, endpoint: str) -> httpx.Response:
        """Send an authenticated GET request to GitHub with retries."""

        max_retries = 3

        for attempt in range(max_retries + 1):
            response = self.client.get(endpoint)

            print(
                "GitHub rate limit:",
                response.headers.get("X-RateLimit-Limit"),
            )

            print(
                "GitHub remaining:",
                response.headers.get("X-RateLimit-Remaining"),
            )

            if response.status_code not in {
                429,
                500,
                502,
                503,
                504,
            }:
                response.raise_for_status()
                return response

            if attempt == max_retries:
                response.raise_for_status()

            delay = self._get_retry_delay(
                response=response,
                attempt=attempt,
            )

            print(
                f"Request failed with {response.status_code}. "
                f"Retrying in {delay:.1f} seconds..."
            )

            time.sleep(delay)

        raise RuntimeError("Unexpected retry loop termination")

    def close(self) -> None:
        """Close the HTTP client."""

        self.client.close()