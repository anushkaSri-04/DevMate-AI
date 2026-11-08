
import base64

from devmate.services.project_profile import (
    detect_project_type,
)


def test_detect_machine_learning_project():
    result = detect_project_type(
        {"Python": 10},
        {"Machine Learning": ["scikit-learn"]},
    )

    assert result == "Machine Learning Project"


def test_detect_ai_application():
    result = detect_project_type(
        {"Python": 10},
        {"LLM Framework": ["langchain"]},
    )

    assert result == "AI Application"


def test_detect_backend_application():
    result = detect_project_type(
        {"Python": 10},
        {"Backend Framework": ["fastapi"]},
    )

    assert result == "Backend Application"


def test_detect_python_project():
    result = detect_project_type(
        {"Python": 5},
        {},
    )

    assert result == "Python Project"


def test_detect_unknown_project():
    result = detect_project_type(
        {},
        {},
    )

    assert result == "Unknown Project Type"


def test_get_project_profile(monkeypatch):
    from devmate.services import project_profile

    snapshot = {
        "repository": "test-owner/test-repo",
        "default_branch": "main",
        "tree_data": {"tree": [], "truncated": False},
    }

    structure = {
        "repository": "test-owner/test-repo",
        "default_branch": "main",
        "language_statistics": {"Python": 10},
        "total_files": 12,
        "total_directories": 3,
        "important_files": [
            {"path": "README.md"},
            {"path": "pyproject.toml"},
        ],
        "truncated": False,
    }

    dependencies = {
        "repository": "test-owner/test-repo",
        "requirements": ["httpx"],
        "pyproject": {
            "main": ["pydantic"],
            "optional": {
                "dev": ["pytest", "ruff"],
            },
        },
        "technologies": {
            "HTTP Client": ["httpx"],
            "Data Validation": ["pydantic"],
            "Testing": ["pytest"],
            "Code Quality": ["ruff"],
        },
        "truncated": False,
    }

    class MockGitHubClient:
        def close(self):
            pass

    monkeypatch.setattr(
        project_profile,
        "GitHubClient",
        MockGitHubClient,
    )

    monkeypatch.setattr(
        project_profile,
        "fetch_repository_snapshot",
        lambda github, owner, repo: snapshot,
    )

    monkeypatch.setattr(
        project_profile,
        "build_repository_structure",
        lambda owner, repo, snapshot: structure,
    )

    monkeypatch.setattr(
        project_profile,
        "build_repository_dependencies",
        lambda github, owner, repo, snapshot: dependencies,
    )

    result = project_profile.get_project_profile(
        "test-owner",
        "test-repo",
    )

    assert result["repository"] == "test-owner/test-repo"
    assert result["default_branch"] == "main"
    assert result["project_type"] == "Python Project"
    assert result["languages"] == {"Python": 10}
    assert result["total_files"] == 12
    assert result["total_directories"] == 3

    assert result["dependencies"]["main"] == [
        "httpx",
        "pydantic",
    ]

    assert result["dependencies"]["development"] == [
        "pytest",
        "ruff",
    ]

    assert result["truncated"] is False


def test_get_project_profile_fetches_repository_snapshot_once(monkeypatch):
    from devmate.services import project_profile

    calls = []

    class FakeResponse:
        def __init__(self, data):
            self.data = data

        def json(self):
            return self.data

    class FakeGitHubClient:
        instances = []

        def __init__(self):
            self.closed = False
            FakeGitHubClient.instances.append(self)

        def get(self, endpoint):
            calls.append(endpoint)

            if endpoint == "/repos/test-owner/test-repo":
                return FakeResponse({
                    "default_branch": "main",
                })

            if "/git/trees/" in endpoint:
                return FakeResponse({
                    "tree": [
                        {
                            "path": "README.md",
                            "type": "blob",
                            "size": 100,
                        },
                        {
                            "path": "requirements.txt",
                            "type": "blob",
                            "size": 20,
                        },
                        {
                            "path": "pyproject.toml",
                            "type": "blob",
                            "size": 100,
                        },
                    ],
                    "truncated": False,
                })

            if endpoint.endswith("/requirements.txt"):
                content = "httpx\n"

            elif endpoint.endswith("/pyproject.toml"):
                content = (
                    '[project]\n'
                    'dependencies = ["pydantic"]\n'
                    '[project.optional-dependencies]\n'
                    'dev = ["pytest"]\n'
                )

            else:
                raise AssertionError(
                    f"Unexpected GitHub API endpoint: {endpoint}"
                )

            encoded = base64.b64encode(
                content.encode()
            ).decode()

            return FakeResponse({
                "encoding": "base64",
                "content": encoded,
            })

        def close(self):
            self.closed = True

    monkeypatch.setattr(
        project_profile,
        "GitHubClient",
        FakeGitHubClient,
    )

    result = project_profile.get_project_profile(
        "test-owner",
        "test-repo",
    )

    assert result["repository"] == "test-owner/test-repo"

    assert calls.count(
        "/repos/test-owner/test-repo"
    ) == 1

    tree_calls = [
        call for call in calls
        if "/git/trees/" in call
    ]
    assert len(tree_calls) == 1

    assert calls.count(
        "/repos/test-owner/test-repo/contents/requirements.txt"
    ) == 1

    assert calls.count(
        "/repos/test-owner/test-repo/contents/pyproject.toml"
    ) == 1

    assert len(FakeGitHubClient.instances) == 1
    assert FakeGitHubClient.instances[0].closed is True