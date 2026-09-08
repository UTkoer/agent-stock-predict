"""MCP tool for writing Markdown files."""

from pathlib import Path


def md_write(file_path: str, content: str) -> dict:
    """Write Markdown content to the requested file path."""
    try:
        if not isinstance(file_path, str) or not file_path.strip():
            raise ValueError("file_path must be a non-empty path")
        if not isinstance(content, str):
            raise ValueError("content must be a string")
        path = Path(file_path).expanduser()
        if path.suffix.lower() not in {".md", ".json"}:
            raise ValueError("file_path must use the .md or .json extension")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(path.resolve()), "bytes": len(content.encode("utf-8"))}
    except Exception as error:
        return {"success": False, "error": str(error)}
