import pytest

from devmate.issue_tools import (
    count_closed_issues,
    count_open_issues,
)


def test_count_open_issues():
    assert count_open_issues(20, 7) == 13


def test_count_open_issues_when_all_are_closed():
    assert count_open_issues(10, 10) == 0


def test_count_open_issues_when_none_are_closed():
    assert count_open_issues(10, 0) == 10


def test_count_open_issues_rejects_negative_counts():
    with pytest.raises(ValueError):
        count_open_issues(-2, 1)


def test_count_open_issues_rejects_too_many_closed_issues():
    with pytest.raises(ValueError):
        count_open_issues(5, 8)


def test_count_closed_issues():
    assert count_closed_issues(20, 13) == 7


def test_count_closed_issues_rejects_too_many_open_issues():
    with pytest.raises(ValueError):
        count_closed_issues(5, 8)