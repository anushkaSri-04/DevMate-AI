
import ast


def get_function_details(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    """Extract details about a function or method."""

    args = node.args

    arguments = [
        arg.arg
        for arg in (
            args.posonlyargs
            + args.args
            + args.kwonlyargs
        )
    ]

    if args.vararg:
        arguments.append(f"*{args.vararg.arg}")

    if args.kwarg:
        arguments.append(f"**{args.kwarg.arg}")

    return {
        "name": node.name,
        "arguments": arguments,
        "line": node.lineno,
        "end_line": node.end_lineno,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "docstring": ast.get_docstring(node),
    }


def get_import_details(tree: ast.Module) -> list:
    """Extract import statements from a Python module."""

    imports = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                    "type": "import",
                })

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append({
                    "module": node.module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "level": node.level,
                    "line": node.lineno,
                    "type": "from_import",
                })

    return sorted(imports, key=lambda item: item["line"])


def is_main_guard(test: ast.expr) -> bool:
    """Check whether an if condition is a Python main guard."""

    if not isinstance(test, ast.Compare):
        return False

    if len(test.ops) != 1 or len(test.comparators) != 1:
        return False

    left = test.left
    right = test.comparators[0]

    def is_name_expr(node):
        return isinstance(node, ast.Name) and node.id == "__name__"

    def is_main_string(node):
        return (
            isinstance(node, ast.Constant)
            and node.value == "__main__"
        )

    return (
        isinstance(test.ops[0], ast.Eq)
        and (
            (is_name_expr(left) and is_main_string(right))
            or (is_main_string(left) and is_name_expr(right))
        )
    )


def get_entry_point_details(tree: ast.Module) -> dict:
    """Detect Python main guards and calls made inside them."""

    main_guards = []

    for node in tree.body:

        if isinstance(node, ast.If) and is_main_guard(node.test):

            calls = []

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue

                if isinstance(child.func, ast.Name):
                    name = child.func.id

                elif isinstance(child.func, ast.Attribute):
                    name = child.func.attr

                else:
                    continue

                calls.append({
                    "name": name,
                    "line": child.lineno,
                })

            calls.sort(key=lambda item: item["line"])

            main_guards.append({
                "line": node.lineno,
                "end_line": node.end_lineno,
                "calls": calls,
                "calls_main": any(
                    call["name"] == "main"
                    for call in calls
                ),
            })

    return {
        "is_entry_point": bool(main_guards),
        "main_guards": main_guards,
    }


def get_call_name(node: ast.expr) -> str | None:
    """Extract the complete dotted name of a function call."""

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = get_call_name(node.value)

        if parent:
            return f"{parent}.{node.attr}"

        return node.attr

    return None


def analyze_python_file(source_file: dict) -> dict:
    """Analyze a Python source file using AST."""

    path = source_file["path"]
    content = source_file["content"]

    try:
        tree = ast.parse(content, filename=path)

    except SyntaxError as error:
        return {
            "file": path,
            "line_count": len(content.splitlines()),
            "functions": [],
            "classes": [],
            "imports": [],
            "function_calls": [],
            "docstring": None,
            "entry_point": {
                "is_entry_point": False,
                "main_guards": [],
            },
            "syntax_error": {
                "message": error.msg,
                "line": error.lineno,
                "column": error.offset,
            },
        }

    functions = []
    classes = []

    for node in tree.body:

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                get_function_details(node)
            )

        elif isinstance(node, ast.ClassDef):

            methods = [
                get_function_details(member)
                for member in node.body
                if isinstance(
                    member,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            ]

            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": node.end_lineno,
                "docstring": ast.get_docstring(node),
                "methods": methods,
            })

    
    function_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            qualified_name = get_call_name(node.func)

            if qualified_name is None:
                continue

            function_calls.append({
                "name": qualified_name.split(".")[-1],
                "qualified_name": qualified_name,
                "line": node.lineno,
            })

    function_calls.sort(key=lambda item: item["line"])


    return {
        "file": path,
        "line_count": len(content.splitlines()),
        "functions": functions,
        "classes": classes,
        "imports": get_import_details(tree),
        "function_calls": function_calls,
        "docstring": ast.get_docstring(tree),
        "entry_point": get_entry_point_details(tree),
        "syntax_error": None,
    }
