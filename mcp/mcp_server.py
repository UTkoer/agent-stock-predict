"""Standard MCP server for the stock data tools.

This server intentionally uses the low-level MCP SDK. LangChain clients can
connect to it through ``langchain-mcp-adapters``.
"""

import json
from pathlib import Path
import sys

from mcp.server import Server
from mcp.server.lowlevel import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.md_write import md_write
from tools.call_logger import log_tool_call


server = Server("agent-stock-predict")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="md_write",
            description="将 Markdown 内容写入指定的 Markdown 文件。",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Markdown 文件保存路径"},
                    "content": {"type": "string", "description": "Markdown 内容"},
                },
                "required": ["file_path", "content"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "md_write":
            file_path = arguments.get("file_path")
            content = arguments.get("content")
            if not isinstance(file_path, str) or not isinstance(content, str):
                raise ValueError("file_path and content must be strings")
            result = md_write(file_path, content)
        else:
            result = {"success": False, "error": f"unknown tool: {name}"}
    except Exception as error:
        result = {"success": False, "error": str(error)}
    # Logging is best-effort: a filesystem problem must not hide the tool result.
    try:
        log_tool_call(name, arguments, result)
    except Exception:
        pass
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agent-stock-predict",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(), experimental_capabilities={}
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
