"""Internal automatic logger for MCP tool calls."""

import json
from datetime import datetime
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


def log_tool_call(tool_name: str, arguments: dict, result: object) -> None:
    """Append one MCP call record to the current day's TXT log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone()
    path = LOG_DIR / f"{now:%Y%m%d}.txt"
    record = {
        "time": now.isoformat(),
        "tool": tool_name,
        "arguments": arguments,
        "result": result,
    }
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
