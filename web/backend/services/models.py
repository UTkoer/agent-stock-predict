import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "agent" / "agent_config.json"


def list_models():
    if not CONFIG.exists():
        return []
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    return [model for model in data.get("models", []) if isinstance(model, dict)]
