
"""Search utilities for DevMate repository analysis."""

from typing import Any


def _normalize(value: str) -> str:
    """Normalize text for case-insensitive searching."""
    return value.strip().lower()


def _get_file_analyses(analysis: dict) -> list:
    """Get analyzed Python files from repository analysis."""
    return analysis.get("files", [])


def _build_result(
    file: str,
    name: str,
    result_type: str,
    line: int | None = None,
    end_line: int | None = None,
    details: dict | None = None,
) -> dict:
    """Build a consistent search result."""
    return {
        "file": file,
        "name": name,
        "type": result_type,
        "line": line,
        "end_line": end_line,
        "details": details or {},
    }


def search_symbols(
    analysis: dict,
    query: str,
    exact: bool = False,
) -> list:
    """Search for functions, classes, and methods by name."""

    query = _normalize(query)

    if not query:
        return []

    results = []

    for file_analysis in _get_file_analyses(analysis):
        file_path = file_analysis["file"]

        # Search top-level functions.
        for function in file_analysis.get("functions", []):
            name = function["name"]
            normalized_name = _normalize(name)

            matched = (
                normalized_name == query
                if exact
                else query in normalized_name
            )

            if matched:
                results.append(
                    _build_result(
                        file=file_path,
                        name=name,
                        result_type="function",
                        line=function.get("line"),
                        end_line=function.get("end_line"),
                        details=function,
                    )
                )

        # Search classes and their methods.
        for cls in file_analysis.get("classes", []):
            class_name = cls["name"]
            normalized_class = _normalize(class_name)

            matched = (
                normalized_class == query
                if exact
                else query in normalized_class
            )

            if matched:
                results.append(
                    _build_result(
                        file=file_path,
                        name=class_name,
                        result_type="class",
                        line=cls.get("line"),
                        end_line=cls.get("end_line"),
                        details=cls,
                    )
                )

            for method in cls.get("methods", []):
                method_name = method["name"]
                normalized_method = _normalize(method_name)

                matched = (
                    normalized_method == query
                    if exact
                    else query in normalized_method
                )

                if matched:
                    results.append(
                        _build_result(
                            file=file_path,
                            name=method_name,
                            result_type="method",
                            line=method.get("line"),
                            end_line=method.get("end_line"),
                            details={
                                **method,
                                "class": class_name,
                            },
                        )
                    )

    return results


def search_functions(
    analysis: dict,
    query: str,
    exact: bool = False,
) -> list:
    """Search only top-level functions."""

    results = []

    for file_analysis in _get_file_analyses(analysis):
        for function in file_analysis.get("functions", []):
            name = function["name"]
            normalized_name = _normalize(name)
            normalized_query = _normalize(query)

            matched = (
                normalized_name == normalized_query
                if exact
                else normalized_query in normalized_name
            )

            if matched:
                results.append(
                    _build_result(
                        file=file_analysis["file"],
                        name=name,
                        result_type="function",
                        line=function.get("line"),
                        end_line=function.get("end_line"),
                        details=function,
                    )
                )

    return results


def search_classes(
    analysis: dict,
    query: str,
    exact: bool = False,
) -> list:
    """Search classes by name."""

    results = []
    normalized_query = _normalize(query)

    for file_analysis in _get_file_analyses(analysis):
        for cls in file_analysis.get("classes", []):
            name = cls["name"]
            normalized_name = _normalize(name)

            matched = (
                normalized_name == normalized_query
                if exact
                else normalized_query in normalized_name
            )

            if matched:
                results.append(
                    _build_result(
                        file=file_analysis["file"],
                        name=name,
                        result_type="class",
                        line=cls.get("line"),
                        end_line=cls.get("end_line"),
                        details=cls,
                    )
                )

    return results


def search_files(
    analysis: dict,
    query: str,
    exact: bool = False,
) -> list:
    """Search analyzed Python files by path or filename."""

    normalized_query = _normalize(query)
    results = []

    if not normalized_query:
        return results

    for file_analysis in _get_file_analyses(analysis):
        file_path = file_analysis["file"]
        normalized_path = _normalize(file_path)

        matched = (
            normalized_path == normalized_query
            if exact
            else normalized_query in normalized_path
        )

        if matched:
            results.append({
                "file": file_path,
                "type": "file",
                "line": None,
                "details": {
                    "line_count": file_analysis.get("line_count", 0),
                    "function_count": len(
                        file_analysis.get("functions", [])
                    ),
                    "class_count": len(
                        file_analysis.get("classes", [])
                    ),
                },
            })

    return results


def search_imports(
    analysis: dict,
    query: str,
) -> list:
    """Search imported modules and imported names."""

    normalized_query = _normalize(query)
    results = []

    if not normalized_query:
        return results

    for file_analysis in _get_file_analyses(analysis):
        for imported in file_analysis.get("imports", []):
            module = imported.get("module") or ""
            imported_name = imported.get("name") or ""
            alias = imported.get("alias") or ""

            searchable = " ".join(
                [module, imported_name, alias]
            ).lower()

            if normalized_query in searchable:
                results.append({
                    "file": file_analysis["file"],
                    "type": "import",
                    "name": imported_name or module,
                    "line": imported.get("line"),
                    "details": imported,
                })

    return results


def search_code_keywords(
    source_files: list[dict],
    query: str,
    case_sensitive: bool = False,
) -> list:
    """
    Search raw source code for keywords.

    source_files must contain:
        path: repository file path
        content: source code string
    """

    if not query:
        return []

    results = []

    search_query = query if case_sensitive else query.lower()

    for source_file in source_files:
        path = source_file.get("path")
        content = source_file.get("content", "")

        if not path or not isinstance(content, str):
            continue

        for line_number, line in enumerate(
            content.splitlines(),
            start=1,
        ):
            searchable_line = (
                line if case_sensitive else line.lower()
            )

            if search_query in searchable_line:
                results.append({
                    "file": path,
                    "type": "keyword",
                    "name": query,
                    "line": line_number,
                    "snippet": line.strip(),
                })

    return results


def find_references(
    analysis: dict,
    query: str,
) -> list:
    """Find function-call references by name or qualified name."""

    normalized_query = _normalize(query)

    if not normalized_query:
        return []

    results = []

    for file_analysis in _get_file_analyses(analysis):
        for call in file_analysis.get("function_calls", []):
            name = call.get("name", "")
            qualified_name = call.get("qualified_name", "")

            searchable = [
                _normalize(name),
                _normalize(qualified_name),
            ]

            if normalized_query in searchable:
                results.append({
                    "file": file_analysis["file"],
                    "type": "function_call",
                    "name": qualified_name or name,
                    "line": call.get("line"),
                    "details": call,
                })

    return results


def get_symbol_definition(
    analysis: dict,
    symbol_name: str,
) -> list:
    """Find exact definitions of a function, class, or method."""

    return search_symbols(
        analysis=analysis,
        query=symbol_name,
        exact=True,
    )


def search_repository(
    analysis: dict,
    query: str,
) -> dict:
    """
    Search repository metadata across symbols, files,
    imports, and function-call references.
    """

    if not query or not query.strip():
        return {
            "query": query,
            "total_results": 0,
            "results": {},
        }

    results = {
        "symbols": search_symbols(analysis, query),
        "files": search_files(analysis, query),
        "imports": search_imports(analysis, query),
        "references": find_references(analysis, query),
    }

    total_results = sum(
        len(items)
        for items in results.values()
    )

    return {
        "query": query,
        "total_results": total_results,
        "results": results,
    }
