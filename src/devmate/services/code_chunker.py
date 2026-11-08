
"""Extract meaningful Python code chunks for DevMate AI embeddings."""

import ast
import hashlib
from pathlib import PurePosixPath
from typing import Any


def _make_chunk(
    file_path: str,
    source_lines: list[str],
    node: ast.AST,
    chunk_type: str,
    symbol_name: str,
    repository: str | None = None,
) -> dict[str, Any]:
    """Create a structured code chunk with source metadata."""

    start_line = getattr(node, "lineno", 1)
    end_line = getattr(node, "end_lineno", start_line)

    code = "\n".join(source_lines[start_line - 1:end_line])

    metadata = {
        "file": file_path,
        "symbol": symbol_name,
        "type": chunk_type,
        "start_line": start_line,
        "end_line": end_line,
        "repository": repository or "",
    }

    # Add descriptive information to improve semantic embeddings.
    searchable_text = (
        f"Repository: {repository or 'unknown'}\n"
        f"File: {file_path}\n"
        f"Symbol: {symbol_name}\n"
        f"Type: {chunk_type}\n"
        f"Lines: {start_line}-{end_line}\n\n"
        f"{code}"
    )

    unique_value = (
        f"{repository}:{file_path}:{chunk_type}:"
        f"{symbol_name}:{start_line}:{end_line}"
    )

    chunk_id = hashlib.sha256(
        unique_value.encode("utf-8")
    ).hexdigest()

    return {
        "id": chunk_id,
        "text": searchable_text,
        "code": code,
        "metadata": metadata,
    }


def _get_symbol_name(node: ast.AST) -> str:
    """Get a readable name for a function or class."""

    return getattr(node, "name", "unknown")


def _extract_class_chunks(
    class_node: ast.ClassDef,
    file_path: str,
    source_lines: list[str],
    repository: str | None,
) -> list[dict[str, Any]]:
    """Extract a class and its methods as separate chunks."""

    chunks = []

    class_chunk = _make_chunk(
        file_path=file_path,
        source_lines=source_lines,
        node=class_node,
        chunk_type="class",
        symbol_name=class_node.name,
        repository=repository,
    )

    chunks.append(class_chunk)

    for child in class_node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_name = f"{class_node.name}.{child.name}"

            method_chunk = _make_chunk(
                file_path=file_path,
                source_lines=source_lines,
                node=child,
                chunk_type="method",
                symbol_name=method_name,
                repository=repository,
            )

            chunks.append(method_chunk)

    return chunks


def chunk_python_file(
    file_path: str,
    content: str,
    repository: str | None = None,
) -> list[dict[str, Any]]:
    """Extract classes, functions and methods from one Python file."""

    if not content or not content.strip():
        return []

    try:
        tree = ast.parse(content)
    except SyntaxError as error:
        print(
            f"Skipping {file_path}: "
            f"Python syntax error at line {error.lineno}"
        )
        return []

    source_lines = content.splitlines()
    chunks = []

    for node in tree.body:

        # Top-level functions.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append(
                _make_chunk(
                    file_path=file_path,
                    source_lines=source_lines,
                    node=node,
                    chunk_type="function",
                    symbol_name=_get_symbol_name(node),
                    repository=repository,
                )
            )

        # Classes and their methods.
        elif isinstance(node, ast.ClassDef):
            chunks.extend(
                _extract_class_chunks(
                    class_node=node,
                    file_path=file_path,
                    source_lines=source_lines,
                    repository=repository,
                )
            )

    # If the file has no functions or classes, index it as a module.
    if not chunks:
        module_node = ast.Module(
            body=tree.body,
            type_ignores=[],
        )

        # Module nodes do not have line numbers, so use the full file.
        start_line = 1
        end_line = len(source_lines)

        code = "\n".join(source_lines)

        searchable_text = (
            f"Repository: {repository or 'unknown'}\n"
            f"File: {file_path}\n"
            f"Symbol: {PurePosixPath(file_path).stem}\n"
            f"Type: module\n"
            f"Lines: {start_line}-{end_line}\n\n"
            f"{code}"
        )

        unique_value = (
            f"{repository}:{file_path}:module:{start_line}:{end_line}"
        )

        chunks.append({
            "id": hashlib.sha256(
                unique_value.encode("utf-8")
            ).hexdigest(),
            "text": searchable_text,
            "code": code,
            "metadata": {
                "file": file_path,
                "symbol": PurePosixPath(file_path).stem,
                "type": "module",
                "start_line": start_line,
                "end_line": end_line,
                "repository": repository or "",
            },
        })

    return chunks


def chunk_repository(
    source_files: list[dict[str, Any]],
    repository: str | None = None,
) -> list[dict[str, Any]]:
    """Extract code chunks from all Python files in a repository."""

    all_chunks = []

    for source_file in source_files:
        file_path = source_file.get("path", "")
        content = source_file.get("content", "")

        if not file_path.endswith(".py"):
            continue

        if not content:
            continue

        chunks = chunk_python_file(
            file_path=file_path,
            content=content,
            repository=repository,
        )

        all_chunks.extend(chunks)

    return all_chunks
