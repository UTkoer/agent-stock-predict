TOOLS = [
    {"name": "md_write", "description": "将预测复盘写入 Markdown 或 JSON 文件", "status": "ready"},
    {"name": "call_logger", "description": "自动记录 MCP 工具调用日志", "status": "internal"},
]


def list_tools():
    return TOOLS
