
import pytest

from devmate.mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_server_registers_all_github_tools():
    """Verify that all expected GitHub tools are registered."""

    tools = await mcp.list_tools()

    registered_tool_names = {
        tool.name for tool in tools
    }

    expected_tool_names = {
        "list_repositories",
        "get_repository_details",
        "list_issues",
        "count_open_issues",
        "analyze_repository",
        "analyze_dependencies",
        "get_project_profile_tool",
        "analyze_repository_code_tool",
        "index_repository_code",
        "ask_repository_question",
}

    assert registered_tool_names == expected_tool_names
