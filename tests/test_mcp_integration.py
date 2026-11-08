
import asyncio

import pytest
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from devmate.mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_client_can_discover_and_call_tools(monkeypatch):
    """Test MCP tool discovery and execution through the client protocol."""

    expected_repositories = [
        {
            "name": "DevMate-AI",
            "full_name": "anushkaSri-04/DevMate-AI",
        }
    ]

    def mock_list_repositories():
        return expected_repositories

    monkeypatch.setattr(
        "devmate.mcp.server.github_list_repositories",
        mock_list_repositories,
    )

    server = mcp._lowlevel_server
    initialization_options = server.create_initialization_options()

    async with create_client_server_memory_streams() as (
        client_streams, 
        server_streams,
        ):
        client_read, client_write = client_streams
        server_read, server_write = server_streams

        server_task = asyncio.create_task(
            server.run(
                server_read,
                server_write,
                initialization_options,
            )
        )

        try:
            async with ClientSession(
                client_read,
                client_write,
            ) as session:
                await session.initialize()

                tools_result = await session.list_tools()

                tool_names = {
                    tool.name for tool in tools_result.tools
                }

                assert tool_names == {
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

                result = await session.call_tool(
                    "list_repositories",
                    arguments={},
                )

                assert not result.is_error
                assert len(result.content) > 0
                assert "DevMate-AI" in result.content[0].text

        finally:
            server_task.cancel()
            await asyncio.gather(
                server_task,
                return_exceptions=True,
            )
