import json
from datetime import date, datetime
from pathlib import Path

import akshare as ak

symbols = ["688981.SH", "688256.SH"]
START_DATE = "20260801"
END_DATE = "20260831"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data_test"


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def download_akshare_data(stock_symbols=symbols, start_date=START_DATE,
                          end_date=END_DATE, output_dir=OUTPUT_DIR):
    output_dir = Path(output_dir)
    written = []
    for symbol in stock_symbols:
        code = symbol.split(".", 1)[0]
        frame = ak.stock_zh_a_hist(symbol=code, period="daily",
                                   start_date=start_date, end_date=end_date,
                                   adjust="")
        if frame is None or frame.empty:
            continue
        for row in frame.to_dict(orient="records"):
            raw_date = row.get("\u65e5\u671f", row.get("date", ""))
            trade_date = str(raw_date).replace("-", "")[:8]
            if not trade_date.isdigit() or len(trade_date) != 8:
                continue
            target = output_dir / symbol / f"{trade_date}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(row, ensure_ascii=False,
                                         default=_json_default, indent=2),
                              encoding="utf-8")
            written.append(target)
    return written


if __name__ == "__main__":
    download_akshare_data()
