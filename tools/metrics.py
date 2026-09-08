"""Evaluate stored stock predictions against realized daily price moves."""

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREDICT_DIR = ROOT / "data" / "predict"
STOCKS_DIR = ROOT / "data" / "stocks"


def _actual_from_market_record(record: dict[str, Any]) -> str | None:
    """Convert a daily market record into UP/DOWN/FLAT."""
    value: Any = record.get("pct_chg", record.get("change"))
    if not isinstance(value, (int, float, str)) or isinstance(value, bool):
        return None
    try:
        change = float(value)
    except (TypeError, ValueError):
        return None
    if change > 0:
        return "UP"
    if change < 0:
        return "DOWN"
    return "FLAT"


def update_result_file(result_file: Path, stocks_dir: Path = STOCKS_DIR) -> dict[str, int]:
    """Update one model/stock result file in place and return update counts."""
    try:
        data = json.loads(result_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"failed to read {result_file}: {error}") from error
    if not isinstance(data, list):
        raise ValueError(f"result file must contain a JSON array: {result_file}")

    stock_code = result_file.stem
    updated = 0
    pending = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        predict_date = item.get("predict_date")
        if not isinstance(predict_date, str) or len(predict_date) != 8:
            pending += 1
            continue
        market_file = stocks_dir / stock_code / f"{predict_date}.json"
        if not market_file.exists():
            item["actual"] = None
            item["correct"] = None
            pending += 1
            continue
        try:
            market_record = json.loads(market_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"failed to read {market_file}: {error}") from error
        actual = _actual_from_market_record(market_record)
        item["actual"] = actual
        prediction = str(item.get("prediction", "")).upper()
        item["correct"] = bool(actual and prediction == actual) if actual else None
        updated += 1

    result_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"updated": updated, "pending": pending}


def update_metrics(predict_dir: Path = PREDICT_DIR, stocks_dir: Path = STOCKS_DIR,
                   model: str | None = None, stock: str | None = None) -> dict[str, int]:
    """Update all matching prediction files and return aggregate counts."""
    if model:
        base = predict_dir / model
        files = sorted((base / "results").glob("*.json")) if base.exists() else []
    else:
        files = sorted(predict_dir.glob("*/results/*.json")) if predict_dir.exists() else []
    if stock:
        files = [path for path in files if path.stem == stock]
    total = {"files": 0, "updated": 0, "pending": 0}
    for result_file in files:
        counts = update_result_file(result_file, stocks_dir)
        total["files"] += 1
        total["updated"] += counts["updated"]
        total["pending"] += counts["pending"]
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill actual/correct fields in prediction result files")
    parser.add_argument("--model", help="Model directory name, optional")
    parser.add_argument("--stock", help="Stock code, optional")
    parser.add_argument("--predict-dir", type=Path, default=PREDICT_DIR)
    parser.add_argument("--stocks-dir", type=Path, default=STOCKS_DIR)
    args = parser.parse_args()
    print(update_metrics(args.predict_dir, args.stocks_dir, args.model, args.stock))


if __name__ == "__main__":
    main()
