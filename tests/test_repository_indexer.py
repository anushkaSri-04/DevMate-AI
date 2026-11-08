from devmate.clients.github_client import GitHubClient
from devmate.services.repository_indexer import RepositoryIndexer
from devmate.tools.repository_tools import fetch_repository_snapshot


def test_index_devmate_repository():
    github = GitHubClient()

    try:
        snapshot = fetch_repository_snapshot(
            github,
            "anushkaSri-04",
            "DevMate-AI",
        )

        indexer = RepositoryIndexer()

        result = indexer.index_repository(
            github=github,
            owner="anushkaSri-04",
            repo="DevMate-AI",
            snapshot=snapshot,
        )

        print("\nINDEXING RESULT:")
        print(result)

        assert result["status"] == "success"

    finally:
        github.close()