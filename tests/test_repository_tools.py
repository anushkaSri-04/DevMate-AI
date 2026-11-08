
import pytest

from devmate.tools.repository_tools import (
    analyze_repository_dependencies,
    analyze_repository_structure,
    calculate_language_statistics,
    detect_important_files,
    detect_technologies,
    parse_pyproject_dependencies,
    parse_requirements,
)


def test_analyze_repository_dependencies_detects_technologies(
    monkeypatch,
):
    from devmate.tools import repository_tools

    dependencies = {
        "requirements": [
            "fastapi",
            "pandas",
            "numpy",
        ],
        "pyproject": {
            "main": ["httpx", "pydantic"],
            "optional": {
                "dev": ["pytest", "ruff"],
            },
        },
    }

    result = repository_tools.detect_technologies(
        dependencies["requirements"]
        + dependencies["pyproject"]["main"]
        + dependencies["pyproject"]["optional"]["dev"]
    )

    assert result == {
    "Backend Framework": ["fastapi"],
    "Data Analysis": ["pandas"],
    "Data Validation": ["pydantic"],
    "HTTP Client": ["httpx"],
    "Numerical Computing": ["numpy"],
    "Testing": ["pytest"],
    "Code Quality": ["ruff"],
}



class MockResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


class MockGitHubClient:
    def __init__(self):
        self.closed = False
        self.calls = []

    def get(self, endpoint):
        self.calls.append(endpoint)

        if endpoint == "/repos/test-owner/test-repo":
            return MockResponse({
                "default_branch": "main"
            })

        if endpoint == "/repos/test-owner/test-repo/git/trees/main?recursive=1":
            return MockResponse({
                "truncated": False,
                "tree": [
                    {
                        "path": "src",
                        "type": "tree",
                    },
                    {
                        "path": "src/main.py",
                        "type": "blob",
                        "size": 120,
                    },
                    {
                        "path": "README.md",
                        "type": "blob",
                        "size": 200,
                    },
                    {
                        "path": "node_modules/package/index.js",
                        "type": "blob",
                        "size": 500,
                    },
                ],
            })

        raise ValueError(f"Unexpected endpoint: {endpoint}")

    def close(self):
        self.closed = True


@pytest.fixture
def mock_github(monkeypatch):
    client = MockGitHubClient()

    monkeypatch.setattr(
        "devmate.tools.repository_tools.GitHubClient",
        lambda: client,
    )

    return client


def test_analyze_repository_structure(mock_github):
    result = analyze_repository_structure(
        "test-owner",
        "test-repo",
    )

    assert result["repository"] == "test-owner/test-repo"
    assert result["default_branch"] == "main"
    assert result["total_files"] == 2
    assert result["total_directories"] == 1
    assert result["truncated"] is False

    file_paths = {
        file["path"] for file in result["files"]
    }

    assert file_paths == {
        "src/main.py",
        "README.md",
    }

    assert "node_modules/package/index.js" not in file_paths


def test_file_extensions_are_detected(mock_github):
    result = analyze_repository_structure(
        "test-owner",
        "test-repo",
    )

    extensions = {
        file["name"]: file["extension"]
        for file in result["files"]
    }

    assert extensions["main.py"] == ".py"
    assert extensions["README.md"] == ".md"


def test_github_client_is_closed(mock_github):
    analyze_repository_structure(
        "test-owner",
        "test-repo",
    )

    assert mock_github.closed is True

def test_calculate_language_statistics():
    files = [
        {"path": "main.py", "extension": ".py"},
        {"path": "app.py", "extension": ".py"},
        {"path": "script.js", "extension": ".js"},
        {"path": "index.ts", "extension": ".ts"},
        {"path": "README.md", "extension": ".md"},
        {"path": "config.toml", "extension": ".toml"},
    ]

    result = calculate_language_statistics(files)

    assert result == {
        "Python": 2,
        "JavaScript": 1,
        "TypeScript": 1,
    }


def test_calculate_language_statistics_empty_files():
    result = calculate_language_statistics([])

    assert result == {}


def test_detect_important_files():
    files = [
        {"path": "README.md", "name": "README.md"},
        {"path": "pyproject.toml", "name": "pyproject.toml"},
        {"path": "src/main.py", "name": "main.py"},
        {"path": "Dockerfile", "name": "Dockerfile"},
    ]

    result = detect_important_files(files)

    assert len(result) == 3

    detected_names = {
        file["name"] for file in result
    }

    assert detected_names == {
        "README.md",
        "pyproject.toml",
        "Dockerfile",
    }


def test_detect_important_files_empty():
    assert detect_important_files([]) == []


def test_parse_requirements():
    content = """
    fastapi>=0.100
    uvicorn
    pandas>=2.0

    # Development dependency
    pytest>=8
    numpy
    """

    result = parse_requirements(content)

    assert result == [
        "fastapi",
        "numpy",
        "pandas",
        "pytest",
        "uvicorn",
    ]



def test_parse_requirements_ignores_pip_options():
    content = """
    -r base.txt
    --index-url https://example.com
    requests>=2.0
    """

    result = parse_requirements(content)

    assert result == ["requests"]


def test_parse_pyproject_dependencies():
    content = """
    [project]
    dependencies = [
        "httpx>=0.27",
        "pydantic>=2.7",
    ]

    [project.optional-dependencies]
    dev = [
        "pytest>=8",
        "ruff>=0.5",
    ]
    """

    result = parse_pyproject_dependencies(content)

    assert result == {
        "main": ["httpx", "pydantic"],
        "optional": {
            "dev": ["pytest", "ruff"],
        },
    }


def test_parse_pyproject_without_dependencies():
    content = """
    [project]
    name = "sample-project"
    version = "1.0.0"
    """

    result = parse_pyproject_dependencies(content)

    assert result == {
        "main": [],
        "optional": {},
    }



def test_analyze_repository_dependencies(monkeypatch):
    from devmate.tools import repository_tools

    class MockResponse:
        def __init__(self, data):
            self.data = data

        def json(self):
            return self.data

    class MockGitHubClient:
        def __init__(self):
            self.closed = False

        def get(self, endpoint):
            if endpoint == "/repos/test-owner/test-repo":
                return MockResponse({
                    "default_branch": "main"
                })

            if endpoint == (
                "/repos/test-owner/test-repo/"
                "git/trees/main?recursive=1"
            ):
                return MockResponse({
                    "truncated": False,
                    "tree": [
                        {
                            "path": "requirements.txt",
                            "type": "blob",
                        },
                        {
                            "path": "pyproject.toml",
                            "type": "blob",
                        },
                    ],
                })

            raise ValueError(f"Unexpected endpoint: {endpoint}")

        def close(self):
            self.closed = True

    client = MockGitHubClient()

    monkeypatch.setattr(
        repository_tools,
        "GitHubClient",
        lambda: client,
    )

    def mock_get_content(github, owner, repo, path):
        contents = {
            "requirements.txt": "fastapi\npandas\n",
            "pyproject.toml": """
[project]
dependencies = ["httpx>=0.27"]

[project.optional-dependencies]
dev = ["pytest>=8"]
""",
        }
        return contents[path]

    monkeypatch.setattr(
        repository_tools,
        "get_repository_file_content",
        mock_get_content,
    )

    result = analyze_repository_dependencies(
        "test-owner",
        "test-repo",
    )

    assert result["requirements"] == [
        "fastapi",
        "pandas",
    ]

    assert result["pyproject"] == {
        "main": ["httpx"],
        "optional": {
            "dev": ["pytest"],
        },
    }

    assert result["files_analyzed"] == [
        "requirements.txt",
        "pyproject.toml",
    ]

    assert client.closed is True


def test_analyze_repository_without_dependency_files(
    monkeypatch,
):
    from devmate.tools import repository_tools

    class MockResponse:
        def json(self):
            return {
                "default_branch": "main"
            }

    class MockTreeResponse:
        def json(self):
            return {
                "truncated": False,
                "tree": [
                    {
                        "path": "README.md",
                        "type": "blob",
                    },
                ],
            }

    class MockGitHubClient:
        def __init__(self):
            self.closed = False

        def get(self, endpoint):
            if endpoint == "/repos/test-owner/test-repo":
                return MockResponse()

            return MockTreeResponse()

        def close(self):
            self.closed = True

    client = MockGitHubClient()

    monkeypatch.setattr(
        repository_tools,
        "GitHubClient",
        lambda: client,
    )

    result = analyze_repository_dependencies(
        "test-owner",
        "test-repo",
    )

    assert result["requirements"] == []
    assert result["pyproject"] == {
        "main": [],
        "optional": {},
    }
    assert result["files_analyzed"] == []
    assert client.closed is True



def test_detect_technologies():
    dependencies = [
        "fastapi",
        "pandas",
        "numpy",
        "tensorflow",
        "langchain",
        "pytest",
        "unknown-package",
    ]

    result = detect_technologies(dependencies)

    assert result == {
        "Backend Framework": ["fastapi"],
        "Data Analysis": ["pandas"],
        "Deep Learning": ["tensorflow"],
        "LLM Framework": ["langchain"],
        "Numerical Computing": ["numpy"],
        "Testing": ["pytest"],
    }


def test_detect_technologies_empty():
    assert detect_technologies([]) == {}


def test_detect_technologies_case_insensitive():
    result = detect_technologies([
        "FastAPI",
        "Pandas",
    ])

    assert result == {
        "Backend Framework": ["FastAPI"],
        "Data Analysis": ["Pandas"],
    }
