"""LangChain client helper for the local stock MCP server."""

from pathlib import Path
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_stock_tools():
    """Return MCP tools converted to LangChain tools."""
    server_path = Path(__file__).resolve() / "mcp_server.py"
    client = MultiServerMCPClient(
        {
            "stock": {
                "command": sys.executable,
                "args": [str(server_path)],
                "transport": "stdio",
            }
        }
    )
    return await client.get_tools()
