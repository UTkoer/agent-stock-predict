import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PREDICT_DIR = ROOT / "data" / "predict"


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "model"


def read_predictions(symbol: str | None = None, model: str | None = None):
    base = PREDICT_DIR / _safe_name(model) / "results" if model else PREDICT_DIR
    files = list(base.glob("**/*.json")) if base.exists() else []
    output = []
    for path in files:
        if symbol and path.stem != symbol:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            for item in data:
                item["model"] = path.parent.parent.name
                item["stock_code"] = path.stem
                output.append(item)
    return sorted(output, key=lambda item: item.get("predict_date", ""), reverse=True)
