
import pytest

from devmate.mcp import server


@pytest.mark.asyncio
async def test_mcp_list_repositories_executes_correctly(monkeypatch):
    """Verify that the MCP tool calls the GitHub repository function."""
    expected_repositories = [
        {
            "name": "DevMate-AI",
            "full_name": "anushkaSri-04/DevMate-AI",
        }
    ]
    def mock_list_repositories():
        return expected_repositories
    monkeypatch.setattr(
        server,
        "github_list_repositories",
        mock_list_repositories,
    )
    result = server.list_repositories()
    assert result == expected_repositories


@pytest.mark.asyncio
async def test_mcp_get_repository_details_executes_correctly(monkeypatch):
    expected = {
        "name": "DevMate-AI",
        "full_name": "anushkaSri-04/DevMate-AI",
    }

    def mock_get_repository_details(owner, repo):
        assert owner == "anushkaSri-04"
        assert repo == "DevMate-AI"
        return expected

    monkeypatch.setattr(
        server,
        "github_get_repository_details",
        mock_get_repository_details,
    )

    result = server.get_repository_details(
        owner="anushkaSri-04",
        repo="DevMate-AI",
    )

    assert result == expected


@pytest.mark.asyncio
async def test_mcp_list_issues_executes_correctly(monkeypatch):
    expected_issues = [
        {"number": 1, "title": "Fix login bug"},
        {"number": 2, "title": "Improve README"},
    ]

    def mock_list_issues(owner, repo, state, per_page, max_pages):
        return expected_issues, True

    monkeypatch.setattr(
        server,
        "github_list_issues",
        mock_list_issues,
    )

    result = server.list_issues(
        owner="anushkaSri-04",
        repo="DevMate-AI",
    )

    assert result == {
        "issues": expected_issues,
        "complete": True,
        "count": 2,
    }


@pytest.mark.asyncio
async def test_mcp_count_open_issues_executes_correctly(monkeypatch):
    expected = {
        "owner": "anushkaSri-04",
        "repository": "DevMate-AI",
        "open_issue_count": 5,
        "complete": True,
    }

    def mock_count_open_issues(owner, repo):
        return expected
    monkeypatch.setattr(
        server,
        "github_count_open_issues",
        mock_count_open_issues,
    )
    result = server.count_open_issues(
        owner="anushkaSri-04",
        repo="DevMate-AI",
    )
    assert result == expected


def test_mcp_list_repositories_propagates_github_error(monkeypatch):
    def mock_list_repositories():
        raise RuntimeError("GitHub API unavailable")
    monkeypatch.setattr(
        server,
        "github_list_repositories",
        mock_list_repositories,
    )
    with pytest.raises(RuntimeError, match="GitHub API unavailable"):
        server.list_repositories()


def test_mcp_get_repository_details_propagates_github_error(monkeypatch):
    def mock_get_repository_details(owner, repo):
        raise RuntimeError("Repository not found")
    monkeypatch.setattr(
        server,
        "github_get_repository_details",
        mock_get_repository_details,
    )
    with pytest.raises(RuntimeError, match="Repository not found"):
        server.get_repository_details(
            owner="anushkaSri-04",
            repo="DevMate-AI",
        )

def test_mcp_get_project_profile_executes_correctly(monkeypatch):
    from devmate.mcp import server

    expected_profile = {
        "repository": "test-owner/test-repo",
        "project_type": "Python Project",
        "total_files": 10,
    }

    def mock_get_project_profile(owner, repo):
        return expected_profile

    monkeypatch.setattr(
        server,
        "get_project_profile",
        mock_get_project_profile,
    )

    result = server.get_project_profile_tool(
        "test-owner",
        "test-repo",
    )

    assert result == expected_profile