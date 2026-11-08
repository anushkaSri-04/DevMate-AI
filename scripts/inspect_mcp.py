import asyncio

from devmate.mcp.server import mcp


async def main():
    tools = await mcp.list_tools()

    print("Registered MCP tools:")
    for tool in tools:
        print(f"- {tool.name}")


if __name__ == "__main__":
    asyncio.run(main())