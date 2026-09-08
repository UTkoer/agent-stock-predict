"""Tushare daily stock data downloader."""

import json
import os
from datetime import date, datetime
from pathlib import Path

import tushare as ts
from dotenv import load_dotenv

load_dotenv()

def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def download_daily_data(symbols, start_date, end_date, output_dir, token=None):
    """Download Tushare daily bars and return the files written."""
    token = token or os.getenv("TUSHARE_TOKEN")
    if not token:
        raise RuntimeError("TUSHARE_TOKEN is not set")

    client = ts.pro_api(token)
    output_dir = Path(output_dir)
    written = []
    for symbol in symbols:
        existing = {path.stem: path for path in (output_dir / symbol).glob("*.json")}
        frame = client.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
        if frame is None or frame.empty:
            print(f"tushare: {symbol} returned no data ({start_date}-{end_date})")
            written.extend(path for day, path in existing.items() if start_date <= day <= end_date)
            continue
        symbol_count = 0
        for row in frame.to_dict(orient="records"):
            trade_date = str(row.get("trade_date", ""))[:8]
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
            symbol_count += 1
        print(f"tushare: {symbol} wrote {symbol_count} day(s)")
    return written
