
from collections import defaultdict
from pathlib import PurePosixPath


def build_module_index(file_analyses: list[dict]) -> dict:
    """Map Python module names and common package aliases to file paths."""

    module_index = {}

    for file_data in file_analyses:
        path = PurePosixPath(file_data["file"])

        if path.name == "__init__.py":
            parts = list(path.parent.parts)
        else:
            parts = list(path.with_suffix("").parts)

        module_name = ".".join(parts)
        module_index[module_name] = str(path)

        # Support src-layout projects:
        # src/devmate/module.py -> devmate.module
        if parts and parts[0] == "src":
            alias = ".".join(parts[1:])
            if alias:
                module_index[alias] = str(path)

    return module_index


def resolve_relative_module(
    importer_path: str,
    module: str | None,
    level: int,
) -> str | None:
    """Convert a relative import into its absolute module name."""

    if level == 0:
        return module

    importer = PurePosixPath(importer_path)
    package_parts = list(importer.parent.parts)

    if importer.name == "__init__.py":
        pass

    elif package_parts and package_parts[0] == "src":
        package_parts = package_parts[1:]

    remove_count = level - 1

    if remove_count:
        package_parts = package_parts[:-remove_count]

    if module:
        package_parts.extend(module.split("."))

    return ".".join(package_parts)


def resolve_import(
    importer_path: str,
    import_data: dict,
    module_index: dict,
) -> dict | None:
    """Resolve an import to a repository module or imported symbol."""

    module = resolve_relative_module(
        importer_path,
        import_data.get("module"),
        import_data.get("level", 0),
    )

    if not module:
        return None

    # Handle: import package.module
    # Handle: from package import function
    target_file = module_index.get(module)

    if target_file:
        return {
            "target": target_file,
            "module": module,
            "imported_name": import_data.get("name"),
            "imported_symbol": import_data.get("name") is not None,
        }

    # Handle: from package import submodule
    imported_name = import_data.get("name")

    if imported_name and imported_name != "*":
        submodule = f"{module}.{imported_name}"
        target_file = module_index.get(submodule)

        if target_file:
            return {
                "target": target_file,
                "module": submodule,
                "imported_name": imported_name,
                "imported_symbol": False,
            }

    return None


def analyze_module_relationships(
    file_analyses: list[dict],
) -> dict:
    """Build repository-wide Python module relationships."""

    module_index = build_module_index(file_analyses)

    dependency_groups = {}
    external_groups = {}
    unresolved_imports = []

    for file_data in file_analyses:
        source_file = file_data["file"]

        for import_data in file_data["imports"]:
            module = import_data.get("module")
            line = import_data["line"]

            resolved = resolve_import(
                source_file,
                import_data,
                module_index,
            )

            if resolved:
                key = (
                    source_file,
                    resolved["target"],
                    resolved["module"],
                    line,
                )

                if key not in dependency_groups:
                    dependency_groups[key] = {
                        "source": source_file,
                        "target": resolved["target"],
                        "module": resolved["module"],
                        "line": line,
                        "imported_names": [],
                        "imported_symbols": [],
                    }

                name = resolved["imported_name"]

                if name:
                    dependency_groups[key]["imported_names"].append(name)

                    if resolved["imported_symbol"]:
                        dependency_groups[key]["imported_symbols"].append(name)

            elif module:
                key = (source_file, module, line)

                if key not in external_groups:
                    external_groups[key] = {
                        "file": source_file,
                        "module": module,
                        "line": line,
                        "imported_names": [],
                    }

                name = import_data.get("name")

                if name:
                    external_groups[key]["imported_names"].append(name)

            else:
                unresolved_imports.append({
                    "file": source_file,
                    "import": import_data,
                })

    dependencies = list(dependency_groups.values())
    external_imports = list(external_groups.values())

    return {
        "total_modules": len({
            path for path in module_index.values()
        }),
        "total_internal_dependencies": len(dependencies),
        "total_external_imports": len(external_imports),
        "total_unresolved_imports": len(unresolved_imports),
        "module_index": module_index,
        "dependencies": dependencies,
        "external_imports": external_imports,
        "unresolved_imports": unresolved_imports,
    }
