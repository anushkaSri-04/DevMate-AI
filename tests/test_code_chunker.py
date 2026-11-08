
from devmate.services.code_chunker import (
    chunk_python_file,
    chunk_repository,
)


sample_code = '''
import os

def authenticate(token):
    return token is not None


class GitHubClient:

    def get(self, endpoint):
        return endpoint

    def close(self):
        pass
'''


def test_chunk_python_file():

    chunks = chunk_python_file(
        file_path="tools/github_client.py",
        content=sample_code,
        repository="anushkaSri-04/DevMate-AI",
    )

    print("\n===== EXTRACTED CHUNKS =====")

    for chunk in chunks:
        print("\nSymbol:", chunk["metadata"]["symbol"])
        print("Type:", chunk["metadata"]["type"])
        print(
            "Lines:",
            chunk["metadata"]["start_line"],
            "-",
            chunk["metadata"]["end_line"],
        )
        print("Code:\n", chunk["code"])

    assert len(chunks) == 4

    symbols = [
        chunk["metadata"]["symbol"]
        for chunk in chunks
    ]

    assert "authenticate" in symbols
    assert "GitHubClient" in symbols
    assert "GitHubClient.get" in symbols
    assert "GitHubClient.close" in symbols

    print("\nCode chunking test passed!")


if __name__ == "__main__":
    test_chunk_python_file()
