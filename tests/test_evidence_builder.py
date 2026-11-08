
from devmate.services.evidence_builder import EvidenceBuilder


def test_build_valid_evidence():
    builder = EvidenceBuilder()

    contexts = [
        {
            "file": "tools\\github_tools.py",
            "symbol": "list_issues",
            "start_line": 10,
            "end_line": 25,
            "snippet": "def list_issues():\n    pass",
            "retrieval_sources": ["lexical", "semantic"],
        }
    ]

    result = builder.build(contexts)

    assert result["total_evidence"] == 1
    assert result["invalid_contexts"] == 0
    assert result["evidence"][0]["file"] == "tools/github_tools.py"
    assert result["evidence"][0]["symbol"] == "list_issues"
    assert result["related_files"] == ["tools/github_tools.py"]


def test_remove_duplicate_evidence():
    builder = EvidenceBuilder()

    context = {
        "file": "tools/github_tools.py",
        "symbol": "list_issues",
        "start_line": 10,
        "end_line": 25,
        "snippet": "def list_issues():\n    pass",
        "retrieval_sources": ["lexical"],
    }

    duplicate = {
        **context,
        "retrieval_sources": ["semantic"],
    }

    result = builder.build([context, duplicate])

    assert result["total_evidence"] == 1
    assert result["duplicate_contexts"] == 1
    assert result["evidence"][0]["retrieval_sources"] == [
        "lexical",
        "semantic",
    ]


def test_reject_invalid_evidence():
    builder = EvidenceBuilder()

    contexts = [
        {
            "file": "tools/github_tools.py",
            "start_line": 0,
            "end_line": 10,
            "snippet": "invalid line range",
        },
        {
            "file": "",
            "start_line": 1,
            "end_line": 5,
            "snippet": "missing file path",
        },
        {
            "file": "tools/github_tools.py",
            "start_line": 1,
            "end_line": 5,
            "snippet": "",
        },
    ]

    result = builder.build(contexts)

    assert result["total_evidence"] == 0
    assert result["invalid_contexts"] == 3
    assert result["evidence"] == []


def test_empty_contexts():
    builder = EvidenceBuilder()

    result = builder.build([])

    assert result["total_evidence"] == 0
    assert result["invalid_contexts"] == 0
    assert result["duplicate_contexts"] == 0
    assert result["related_files"] == []
