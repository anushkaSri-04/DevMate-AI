
from collections import defaultdict
import builtins
from typing import Any


# ============================================================
# BASIC HELPERS
# ============================================================

def _get_file_path(file_analysis: dict[str, Any]) -> str:
    """Return the source path from a file analysis."""
    return (
        file_analysis.get("path")
        or file_analysis.get("file")
        or file_analysis.get("file_path")
        or ""
    )


def _get_dependencies(
    module_relationships: dict[str, Any],
) -> list[dict[str, Any]]:
    """Safely retrieve module dependency records."""
    return module_relationships.get("dependencies", []) or []


def _get_imported_symbols(dependency: dict[str, Any]) -> list[str]:
    """Return imported symbols from a dependency record."""
    symbols = dependency.get("imported_symbols", [])
    return symbols if isinstance(symbols, list) else []


def _get_imported_names(dependency: dict[str, Any]) -> list[str]:
    """Return imported names or aliases from a dependency record."""
    names = dependency.get("imported_names", [])
    return names if isinstance(names, list) else []


def _normalize_import_record(import_record: Any) -> dict[str, Any]:
    """Normalize different possible import record formats."""
    if isinstance(import_record, str):
        return {
            "module": import_record,
            "name": None,
            "alias": None,
        }

    if isinstance(import_record, dict):
        return {
            "module": (
                import_record.get("module")
                or import_record.get("module_name")
                or import_record.get("from")
                or ""
            ),
            "name": (
                import_record.get("name")
                or import_record.get("imported_name")
                or import_record.get("symbol")
            ),
            "alias": (
                import_record.get("alias")
                or import_record.get("asname")
                or import_record.get("local_name")
            ),
        }

    return {
        "module": "",
        "name": None,
        "alias": None,
    }


def _get_import_information(
    file_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return normalized import information from a file analysis."""
    imports = file_analysis.get("imports", []) or []

    return [
        _normalize_import_record(item)
        for item in imports
    ]


# ============================================================
# SYMBOL INDEX
# ============================================================

def build_symbol_index(
    file_analyses: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Build an index of functions, classes, and methods.

    A symbol can have multiple definitions across files.
    """
    symbol_index = defaultdict(list)

    for file_analysis in file_analyses:
        file_path = _get_file_path(file_analysis)

        if not file_path:
            continue

        # Functions
        for function in file_analysis.get("functions", []):
            name = function.get("name")

            if not name:
                continue

            symbol_index[name].append({
                "name": name,
                "path": file_path,
                "line": function.get("line"),
                "end_line": function.get("end_line"),
                "type": "function",
            })

        # Classes and methods
        for class_info in file_analysis.get("classes", []):
            class_name = class_info.get("name")

            if class_name:
                symbol_index[class_name].append({
                    "name": class_name,
                    "path": file_path,
                    "line": class_info.get("line"),
                    "end_line": class_info.get("end_line"),
                    "type": "class",
                })

            for method in class_info.get("methods", []):
                method_name = method.get("name")

                if not method_name:
                    continue

                symbol_index[method_name].append({
                    "name": method_name,
                    "path": file_path,
                    "line": method.get("line"),
                    "end_line": method.get("end_line"),
                    "type": "method",
                    "class_name": class_name,
                })

    return dict(symbol_index)


# ============================================================
# DIRECT IMPORT BINDINGS
# ============================================================

def build_import_bindings(
    file_analyses: list[dict[str, Any]],
    module_relationships: dict[str, Any],
) -> tuple[dict[str, dict[str, dict[str, Any]]], list[dict[str, Any]]]:
    """
    Resolve direct imports such as:

        from tools.github_tools import list_repositories

        from tools.github_tools import (
            list_repositories as get_repos
        )
    """
    imported_bindings = defaultdict(dict)
    unresolved_imports = []

    dependencies = _get_dependencies(module_relationships)
    symbol_index = build_symbol_index(file_analyses)

    for dependency in dependencies:
        source = dependency.get("source")
        target = dependency.get("target")
        line = dependency.get("line")

        if not source or not target:
            continue

        imported_symbols = _get_imported_symbols(dependency)
        imported_names = _get_imported_names(dependency)

        if not imported_symbols:
            continue

        for index, imported_symbol in enumerate(imported_symbols):
            local_name = (
                imported_names[index]
                if index < len(imported_names) and imported_names[index]
                else imported_symbol
            )

            candidates = [
                definition
                for definition in symbol_index.get(imported_symbol, [])
                if definition["path"] == target
            ]

            if candidates:
                imported_bindings[source][local_name] = {
                    "imported_name": imported_symbol,
                    "local_name": local_name,
                    "source": source,
                    "target": target,
                    "import_line": line,
                    "definition": candidates[0],
                }

            else:
                unresolved_imports.append({
                    "source": source,
                    "target": target,
                    "imported_name": imported_symbol,
                    "local_name": local_name,
                    "line": line,
                    "reason": "Symbol definition not found in target file",
                })

    return dict(imported_bindings), unresolved_imports


# ============================================================
# MODULE IMPORT BINDINGS
# ============================================================

def build_module_bindings(
    file_analyses: list[dict[str, Any]],
    module_relationships: dict[str, Any],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """
    Build bindings for module imports such as:

        import tools.github_tools

        import tools.github_tools as gh
    """
    module_bindings = defaultdict(lambda: defaultdict(list))

    dependencies = _get_dependencies(module_relationships)

    for dependency in dependencies:
        source = dependency.get("source")
        target = dependency.get("target")
        module_name = dependency.get("module")

        if not source or not target or not module_name:
            continue

        imported_symbols = _get_imported_symbols(dependency)

        # Direct symbol imports are handled separately.
        if imported_symbols:
            continue

        imported_names = _get_imported_names(dependency)
        aliases = imported_names or [module_name]

        for alias in aliases:
            if not alias:
                continue

            binding = {
                "module": module_name,
                "target": target,
                "line": dependency.get("line"),
                "local_name": alias,
            }

            module_bindings[source][alias].append(binding)

            # Support unaliased imports:
            # import tools.github_tools
            if alias == module_name and "." in module_name:
                root_name = module_name.split(".")[0]

                root_binding = {
                    "module": module_name,
                    "target": target,
                    "line": dependency.get("line"),
                    "local_name": root_name,
                }

                module_bindings[source][root_name].append(root_binding)

    return {
        source: dict(bindings)
        for source, bindings in module_bindings.items()
    }


# ============================================================
# MODULE BINDING LOOKUP
# ============================================================

def _find_module_binding(
    qualified_name: str,
    source_path: str,
    module_bindings: dict[str, dict[str, list[dict[str, Any]]]],
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Find the module binding matching a dotted function call.

    Examples:

        gh.list_repositories()

        tools.github_tools.list_repositories()
    """
    source_bindings = module_bindings.get(source_path, {})

    matching_aliases = sorted(
        source_bindings.keys(),
        key=len,
        reverse=True,
    )

    for alias in matching_aliases:
        if not qualified_name.startswith(alias + "."):
            continue

        remaining_name = qualified_name[len(alias) + 1:]

        for binding in source_bindings[alias]:
            module_name = binding["module"]

            # Example: gh.list_repositories()
            if alias != module_name:
                return binding, remaining_name.split(".")[-1]

            # Example: tools.github_tools.list_repositories()
            if module_name.startswith(alias + "."):
                module_suffix = module_name[len(alias) + 1:]

                if remaining_name.startswith(module_suffix + "."):
                    member = remaining_name[len(module_suffix) + 1:]
                    return binding, member.split(".")[-1]

            return binding, remaining_name.split(".")[-1]

    return None, None


# ============================================================
# SYMBOL DEFINITION LOOKUP
# ============================================================

def _find_definition(
    symbol_name: str,
    target_path: str,
    symbol_index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    """Find a symbol definition inside a specific target file."""
    for definition in symbol_index.get(symbol_name, []):
        if definition["path"] == target_path:
            return definition

    return None


# ============================================================
# IMPORT CLASSIFICATION
# ============================================================

def _get_imported_roots(
    file_analysis: dict[str, Any],
) -> set[str]:
    """
    Extract imported module roots and aliases.

    Supports common import record formats.
    """
    imported_roots = set()

    for record in _get_import_information(file_analysis):
        module = record.get("module")
        name = record.get("name")
        alias = record.get("alias")

        if module:
            imported_roots.add(module.split(".")[0])

        if alias:
            imported_roots.add(alias.split(".")[0])

        if name:
            imported_roots.add(name.split(".")[0])

    return imported_roots


def _get_imported_symbol_names(
    file_analysis: dict[str, Any],
) -> set[str]:
    """Extract directly imported symbol names and aliases."""
    imported_names = set()

    for record in _get_import_information(file_analysis):
        name = record.get("name")
        alias = record.get("alias")

        if name:
            imported_names.add(name)

        if alias:
            imported_names.add(alias)

    return imported_names


# ============================================================
# UNRESOLVED CALL CLASSIFICATION
# ============================================================

def classify_unresolved_call(
    call_name: str,
    qualified_name: str,
    symbol_index: dict[str, list[dict[str, Any]]],
    file_analysis: dict[str, Any],
    module_bindings: dict[str, dict[str, list[dict[str, Any]]]],
) -> tuple[str, str]:
    """
    Classify calls that could not be resolved to repository definitions.

    Important:
    A method name such as get() must not be classified as a local
    repository function simply because another file defines get().
    """

    # 1. Python built-ins
    if call_name in dir(builtins):
        return (
            "builtin_call",
            "Python built-in function or class",
        )

    # 2. Dotted calls
    if "." in qualified_name:
        root_name = qualified_name.split(".")[0]

        imported_roots = _get_imported_roots(file_analysis)

        # Imported module call, e.g. respx.get()
        if root_name in imported_roots:
            return (
                "external_library_call",
                "Call through an imported external module",
            )

        # Internal module was imported but member was not resolved.
        source_bindings = module_bindings.get(
            _get_file_path(file_analysis),
            {},
        )

        if root_name in source_bindings:
            return (
                "unresolved_module_call",
                "Imported repository module member could not be resolved",
            )

        # Object methods, e.g. github.get(), response.json()
        return (
            "object_method_call",
            "Method call through an object whose definition could not be resolved",
        )

    # 3. Direct external imports
    imported_symbols = _get_imported_symbol_names(file_analysis)

    if call_name in imported_symbols:
        return (
            "external_library_call",
            "Directly imported symbol whose definition is outside the repository",
        )

    # 4. Repository symbol exists but could not be resolved
    if call_name in symbol_index:
        return (
            "unresolved_local_call",
            "Matching repository symbol exists but could not be resolved to a unique definition",
        )

    # 5. Unknown call
    return (
        "unknown_call",
        "Unable to determine the origin of this call",
    )


# ============================================================
# REFERENCE RECORD HELPERS
# ============================================================

def _make_resolved_reference(
    name: str,
    qualified_name: str,
    source_path: str,
    target_path: str,
    call_line: int | None,
    definition: dict[str, Any],
    reference_type: str,
) -> dict[str, Any]:
    """Create a consistent resolved reference record."""
    return {
        "name": name,
        "symbol": name,
        "qualified_name": qualified_name,
        "source": source_path,
        "source_file": source_path,
        "target": target_path,
        "target_file": target_path,
        "line": call_line,
        "call_line": call_line,
        "definition_line": definition.get("line"),
        "definition": definition,
        "reference_type": reference_type,
        "resolved": True,
    }


def _make_unresolved_reference(
    name: str,
    qualified_name: str,
    source_path: str,
    call_line: int | None,
    reference_type: str,
    reason: str,
    target_path: str | None = None,
) -> dict[str, Any]:
    """Create a consistent unresolved reference record."""
    return {
        "name": name,
        "symbol": name,
        "qualified_name": qualified_name,
        "source": source_path,
        "source_file": source_path,
        "target": target_path,
        "target_file": target_path,
        "line": call_line,
        "call_line": call_line,
        "definition_line": None,
        "definition": None,
        "reference_type": reference_type,
        "resolved": False,
        "reason": reason,
    }


# ============================================================
# MAIN CROSS-FILE ANALYSIS
# ============================================================

def analyze_cross_file_references(
    file_analyses: list[dict[str, Any]],
    module_relationships: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyze function and method references across a Python repository.

    Resolution order:

        1. Module-qualified repository calls
        2. Direct imported repository calls
        3. Same-file functions, classes and methods
        4. Classification of remaining calls

    This is static analysis. Repository code is never executed.
    """

    symbol_index = build_symbol_index(file_analyses)

    imported_bindings, unresolved_imports = build_import_bindings(
        file_analyses,
        module_relationships,
    )

    module_bindings = build_module_bindings(
        file_analyses,
        module_relationships,
    )

    references = []
    unresolved_references = []
    imported_by = {}

    # --------------------------------------------------------
    # Reverse import information
    # --------------------------------------------------------

    def add_import_reference(
        symbol: str,
        target: str,
        reference: dict[str, Any],
    ) -> None:
        key = (symbol, target)

        if key not in imported_by:
            imported_by[key] = {
                "symbol": symbol,
                "target_file": target,
                "references": [],
            }

        imported_by[key]["references"].append(reference)

    # Direct imports
    for source, bindings in imported_bindings.items():
        for local_name, binding in bindings.items():
            add_import_reference(
                binding["imported_name"],
                binding["target"],
                {
                    "file": source,
                    "source": source,
                    "local_name": local_name,
                    "line": binding["import_line"],
                    "type": "direct_import",
                },
            )

    # Module imports
    for source, bindings in module_bindings.items():
        for alias, module_records in bindings.items():
            for binding in module_records:
                add_import_reference(
                    binding["module"],
                    binding["target"],
                    {
                        "file": source,
                        "source": source,
                        "local_name": alias,
                        "line": binding["line"],
                        "type": "module_import",
                    },
                )

    # --------------------------------------------------------
    # Resolve function calls
    # --------------------------------------------------------

    for file_analysis in file_analyses:
        source_path = _get_file_path(file_analysis)

        if not source_path:
            continue

        source_imports = imported_bindings.get(source_path, {})

        for call in file_analysis.get("function_calls", []):
            call_name = call.get("name")

            if not call_name:
                continue

            qualified_name = (
                call.get("qualified_name")
                or call_name
            )

            call_line = call.get("line")

            # ------------------------------------------------
            # 1. Module-qualified repository calls
            # ------------------------------------------------

            if "." in qualified_name:
                module_binding, member_name = _find_module_binding(
                    qualified_name,
                    source_path,
                    module_bindings,
                )

                if module_binding and member_name:
                    target_path = module_binding["target"]

                    definition = _find_definition(
                        member_name,
                        target_path,
                        symbol_index,
                    )

                    if definition:
                        references.append(
                            _make_resolved_reference(
                                name=member_name,
                                qualified_name=qualified_name,
                                source_path=source_path,
                                target_path=target_path,
                                call_line=call_line,
                                definition=definition,
                                reference_type="module_qualified_call",
                            )
                        )

                    else:
                        unresolved_references.append(
                            _make_unresolved_reference(
                                name=member_name,
                                qualified_name=qualified_name,
                                source_path=source_path,
                                call_line=call_line,
                                reference_type="unresolved_module_call",
                                reason=(
                                    "Symbol definition not found "
                                    "in imported repository module"
                                ),
                                target_path=target_path,
                            )
                        )

                    continue

            # ------------------------------------------------
            # 2. Direct imported repository calls
            # ------------------------------------------------

            binding = source_imports.get(call_name)

            if binding:
                definition = binding["definition"]

                references.append(
                    _make_resolved_reference(
                        name=call_name,
                        qualified_name=qualified_name,
                        source_path=source_path,
                        target_path=binding["target"],
                        call_line=call_line,
                        definition=definition,
                        reference_type="direct_import_call",
                    )
                )

                continue

            # ------------------------------------------------
            # 3. Same-file functions, classes and methods
            # ------------------------------------------------

            local_candidates = [
                definition
                for definition in symbol_index.get(call_name, [])
                if definition["path"] == source_path
            ]

            if qualified_name.startswith(("self.", "cls.")):
                local_candidates = [
                    definition
                    for definition in local_candidates
                    if definition["type"] == "method"
                ]

            elif "." not in qualified_name:
                local_candidates = [
                    definition
                    for definition in local_candidates
                    if definition["type"] in ("function", "class")
                ]

            else:
                local_candidates = []

            if len(local_candidates) == 1:
                definition = local_candidates[0]

                references.append(
                    _make_resolved_reference(
                        name=call_name,
                        qualified_name=qualified_name,
                        source_path=source_path,
                        target_path=source_path,
                        call_line=call_line,
                        definition=definition,
                        reference_type="same_file_call",
                    )
                )

                continue

            # ------------------------------------------------
            # 4. Classify calls that remain unresolved
            # ------------------------------------------------

            category, reason = classify_unresolved_call(
                call_name=call_name,
                qualified_name=qualified_name,
                symbol_index=symbol_index,
                file_analysis=file_analysis,
                module_bindings=module_bindings,
            )

            unresolved_references.append(
                _make_unresolved_reference(
                    name=call_name,
                    qualified_name=qualified_name,
                    source_path=source_path,
                    call_line=call_line,
                    reference_type=category,
                    reason=reason,
                )
            )

    # --------------------------------------------------------
    # Convert symbol index into report-friendly definitions
    # --------------------------------------------------------

    definitions = []

    for symbol_name, symbol_definitions in symbol_index.items():
        for definition in symbol_definitions:
            definitions.append({
                "name": definition["name"],
                "file": definition["path"],
                "path": definition["path"],
                "line": definition.get("line"),
                "end_line": definition.get("end_line"),
                "type": definition["type"],
            })

    # --------------------------------------------------------
    # Summary counts
    # --------------------------------------------------------

    total_symbols = len(definitions)
    total_references = len(references)
    total_unresolved_references = len(unresolved_references)

    reference_type_counts = defaultdict(int)

    for reference in references:
        reference_type_counts[reference["reference_type"]] += 1

    for reference in unresolved_references:
        reference_type_counts[reference["reference_type"]] += 1

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    return {
        "total_symbols": total_symbols,
        "total_symbol_names": len(symbol_index),

        "total_references": total_references,
        "total_resolved_references": total_references,

        "total_resolved_imports": sum(
            len(bindings)
            for bindings in imported_bindings.values()
        ),

        "total_unresolved_references": total_unresolved_references,

        "definitions": definitions,
        "symbol_index": symbol_index,

        "imported_bindings": imported_bindings,
        "module_bindings": module_bindings,
        "imported_by": list(imported_by.values()),

        "references": references,
        "unresolved_imports": unresolved_imports,
        "unresolved_references": unresolved_references,

        "reference_type_counts": dict(reference_type_counts),
    }
