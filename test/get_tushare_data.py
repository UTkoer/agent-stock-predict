import json
import os
from datetime import date, datetime
from pathlib import Path

import tushare as ts
from dotenv import load_dotenv

load_dotenv()
symbols = ["601816.SH", "601127.SH"]
token = os.getenv("TUSHARE_TOKEN")

START_DATE = "20260801"
END_DATE = "20260831"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data_test"


def _json_default(value):
    """Serialize pandas/numpy scalar values returned by Tushare."""
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def download_tushare_data(
    stock_symbols=symbols,
    start_date=START_DATE,
    end_date=END_DATE,
    output_dir=OUTPUT_DIR,
    tushare_token=token,
):
    if not tushare_token:
        raise RuntimeError("TUSHARE_TOKEN is not set")

    pro = ts.pro_api(tushare_token)
    output_dir = Path(output_dir)
    written = []
    for symbol in stock_symbols:
        frame = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
        if frame is None or frame.empty:
            continue
        for row in frame.to_dict(orient="records"):
            trade_date = str(row.get("trade_date", ""))[:8]
            if not trade_date:
                continue
            target = output_dir / symbol / f"{trade_date}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(row, ensure_ascii=False, default=_json_default, indent=2), encoding="utf-8")
            written.append(target)
    return written


if __name__ == "__main__":
    download_tushare_data()
