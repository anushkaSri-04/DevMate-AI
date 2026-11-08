
from devmate.services.repository_code_analysis import (
    get_repository_code_analysis,
)

from devmate.services.code_search import (
    search_symbols,
    search_functions,
    search_classes,
    search_files,
    search_imports,
    find_references,
    get_symbol_definition,
    search_repository,
)


OWNER = "anushkaSri-04"
REPO = "DevMate-AI"


analysis = get_repository_code_analysis(OWNER, REPO)


print("\n===== SYMBOL SEARCH =====")
print(search_symbols(analysis, "github"))

print("\n===== FUNCTION SEARCH =====")
print(search_functions(analysis, "list_issues"))

print("\n===== CLASS SEARCH =====")
print(search_classes(analysis, "GitHub"))

print("\n===== FILE SEARCH =====")
print(search_files(analysis, "github_tools"))

print("\n===== IMPORT SEARCH =====")
print(search_imports(analysis, "github"))

print("\n===== REFERENCE SEARCH =====")
print(find_references(analysis, "list_issues"))

print("\n===== SYMBOL DEFINITION =====")
print(get_symbol_definition(analysis, "list_issues"))

print("\n===== COMPLETE REPOSITORY SEARCH =====")
print(search_repository(analysis, "github"))
