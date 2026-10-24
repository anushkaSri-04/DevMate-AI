import pytest

from tools.github_tools import list_issues


def test_invalid_state():
    with pytest.raises(ValueError):
        list_issues(
            "anushkaSri-04",
            "AI_Resume_Analyzer",
            state="invalid",
        )


def test_invalid_per_page():
    with pytest.raises(ValueError):
        list_issues(
            "anushkaSri-04",
            "AI_Resume_Analyzer",
            per_page=101,
        )


def test_invalid_max_pages():
    with pytest.raises(ValueError):
        list_issues(
            "anushkaSri-04",
            "AI_Resume_Analyzer",
            max_pages=11,
        )