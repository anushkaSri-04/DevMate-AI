
"""Run a real Gemini-powered Q&A test against a GitHub repository."""

from devmate.clients.github_client import GitHubClient
from devmate.tools.repository_tools import fetch_repository_snapshot

from devmate.services.repository_code_analysis import (
    analyze_repository_code,
)
from devmate.services.repository_indexer import RepositoryIndexer
from devmate.services.repository_qa import RepositoryQA


OWNER = "anushkaSri-04"
REPO = "DevMate-AI"

QUESTION = (
    "Trace how list_repositories() uses GitHubClient "
    "to retrieve repositories. Explain the complete "
    "execution flow across the relevant files."
)


def main():
    repository = f"{OWNER}/{REPO}"
    github = GitHubClient()

    try:
        print("\n===== DEV MATE AI: LIVE GEMINI TEST =====")

        # 1. Fetch the latest GitHub repository snapshot.
        print("\n[1/5] Fetching GitHub repository...")

        snapshot = fetch_repository_snapshot(
            github,
            OWNER,
            REPO,
        )

        print("Repository:", repository)
        print("Default branch:", snapshot["default_branch"])

        # 2. Index the GitHub repository for semantic retrieval.
        print("\n[2/5] Indexing repository for hybrid retrieval...")

        indexer = RepositoryIndexer()

        indexing_result = indexer.index_repository(
            github=github,
            owner=OWNER,
            repo=REPO,
            snapshot=snapshot,
        )

        print("Indexing status:", indexing_result["status"])
        print("Chunks stored:", indexing_result["total_chunks_stored"])

        # 3. Analyze repository source code.
        print("\n[3/5] Analyzing repository code...")

        analysis = analyze_repository_code(
            github=github,
            owner=OWNER,
            repo=REPO,
            snapshot=snapshot,
        )

        source_files = analysis["source_files"]

        print("Python files analyzed:",
              analysis["summary"]["total_files_analyzed"])

    finally:
        github.close()

    # 4. Ask the actual Gemini model.
    print("\n[4/5] Sending question to Gemini...")

    qa = RepositoryQA()

    result = qa.answer(
        analysis=analysis,
        source_files=source_files,
        question=QUESTION,
        repository=repository,
        max_contexts=8,
        session_id="live-gemini-test",
    )

    # 5. Display the actual response and supporting evidence.
    print("\n===== GEMINI ANSWER =====")
    print("Status:", result["status"])
    print("Model:", result["model"])
    print("\nQuestion:", result["question"])
    print("\nAnswer:\n")
    print(result["answer"])

    print("\n===== SOURCE EVIDENCE =====")

    for index, item in enumerate(result["evidence"], start=1):
        print(f"\nEvidence {index}")
        print("File:", item["file"])
        print("Symbol:", item["symbol"])
        print(
            "Lines:",
            f'{item["start_line"]}-{item["end_line"]}',
        )
        print("Retrieved through:", item["retrieval_sources"])
        print("Snippet:")
        print(item["snippet"])

    print("\n===== RETRIEVAL STATISTICS =====")

    for key, value in result["retrieval"].items():
        print(f"{key}: {value}")

    print("\n===== LIVE GEMINI TEST COMPLETED =====")


if __name__ == "__main__":
    main()
