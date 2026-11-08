from devmate.clients.github_client import GitHubClient

from devmate.services.source_code import (
    retrieve_python_source_files,
)

from devmate.services.repository_code_analysis import (
    analyze_repository_code,
)

from devmate.services.hybrid_retrieval import (
    HybridRetriever,
)

from devmate.tools.repository_tools import (
    fetch_repository_snapshot,
)


OWNER = "anushkaSri-04"
REPO = "DevMate-AI"


def test_hybrid_retrieval():

    github = GitHubClient()

    try:
        # 1. Fetch repository snapshot.
        snapshot = fetch_repository_snapshot(
            github,
            OWNER,
            REPO,
        )

        # 2. Retrieve Python source files.
        source_result = retrieve_python_source_files(
            github,
            OWNER,
            REPO,
            snapshot,
        )

        source_files = source_result["files"]

        # 3. Generate AST and cross-file analysis.
        analysis = analyze_repository_code(
            github,
            OWNER,
            REPO,
            snapshot,
        )

        # 4. Initialize hybrid retriever.
        retriever = HybridRetriever()

        # 5. Test natural-language questions.
        queries = [
            "How does DevMate retrieve GitHub issues?",
            "Where is GitHub authentication handled?",
            "How does the repository indexer generate embeddings?",
        ]

        for query in queries:

            print("\n" + "=" * 65)
            print("QUERY:", query)
            print("=" * 65)

            result = retriever.retrieve(
                analysis=analysis,
                source_files=source_files,
                query=query,
                repository=f"{OWNER}/{REPO}",
                max_contexts=5,
                semantic_top_k=10,
            )

            print("\nLEXICAL RESULTS:", result["lexical_results"])
            print("SEMANTIC RESULTS:", result["semantic_results"])
            print("TOTAL CANDIDATES:", result["total_candidates"])

            print("\nTOP RETRIEVED CONTEXTS:")

            for index, context in enumerate(
                result["contexts"],
                start=1,
            ):
                print(f"\n{index}. {context.get('symbol')}")
                print("File:", context["file"])
                print(
                    "Lines:",
                    context["start_line"],
                    "-",
                    context["end_line"],
                )
                print(
                    "Sources:",
                    context["retrieval_sources"],
                )
                print("RRF Score:", context["rrf_score"])

            assert result["total_contexts"] > 0
            assert result["semantic_results"] > 0

    finally:
        github.close()