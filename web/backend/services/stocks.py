import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STOCKS_DIR = ROOT / "data" / "stocks"


def list_symbols():
    return sorted(path.name for path in STOCKS_DIR.iterdir() if path.is_dir()) if STOCKS_DIR.exists() else []


def read_stock(symbol: str, start_date: str | None = None, end_date: str | None = None):
    directory = STOCKS_DIR / symbol
    if not directory.is_dir():
        raise FileNotFoundError(f"股票不存在: {symbol}")
    rows = []
    for path in sorted(directory.glob("*.json")):
        if not path.stem.isdigit():
            continue
        if start_date and path.stem < start_date:
            continue
        if end_date and path.stem > end_date:
            continue
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows
