"""Read generated Markdown reports for the selected prediction."""
from datetime import datetime
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
PREDICT_DIR = ROOT / "data" / "predict"

def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "model"

def read_report(symbol: str, model: str, predict_date: str) -> str:
    try:
        report_date = datetime.strptime(predict_date, "%Y%m%d").strftime("%y%m%d")
    except ValueError as error:
        raise ValueError("predict_date must be YYYYMMDD") from error
    path = PREDICT_DIR / _safe_name(model) / "markdown" / _safe_name(symbol) / f"{report_date}.md"
    if not path.is_file():
        raise FileNotFoundError(f"Report not found for {symbol} {model} {predict_date}")
    return path.read_text(encoding="utf-8")
