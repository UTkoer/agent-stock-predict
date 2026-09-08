import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILE = ROOT / "agent" / "prompt" / "addtional_prompt.json"


def read_prompt():
    if not PROMPT_FILE.exists():
        return {"default_prompt": ""}
    return json.loads(PROMPT_FILE.read_text(encoding="utf-8"))
