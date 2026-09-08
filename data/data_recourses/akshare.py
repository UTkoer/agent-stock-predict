"""AkShare daily stock data downloader."""

import json
from datetime import date, datetime
from pathlib import Path

import akshare as ak


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def download_daily_data(symbols, start_date, end_date, output_dir):
    """Download AkShare daily bars and return the files written."""
    output_dir = Path(output_dir)
    written = []
    for symbol in symbols:
        code = symbol.split(".", 1)[0]
        existing = {path.stem: path for path in (output_dir / symbol).glob("*.json")}
        frame = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="",
        )
        if frame is None or frame.empty:
            written.extend(path for day, path in existing.items() if start_date <= day <= end_date)
            continue
        for row in frame.to_dict(orient="records"):
            raw_date = row.get("\u65e5\u671f", row.get("date", ""))
            trade_date = str(raw_date).replace("-", "")[:8]
            if len(trade_date) != 8 or not trade_date.isdigit():
                continue
            path = output_dir / symbol / f"{trade_date}.json"
            if path.exists():
                written.append(path)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(row, ensure_ascii=False, default=_json_default, indent=2),
                encoding="utf-8",
            )
            written.append(path)
    return written
