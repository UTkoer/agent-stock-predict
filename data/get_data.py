"""Download configured stock data sources into data/stocks."""

import argparse
import json
from datetime import date, timedelta
from importlib import import_module
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
SYMBOLS_PATH = Path(__file__).resolve().parent / "symbols.json"
OUTPUT_DIR = Path(__file__).resolve().parent / "stocks"
SOURCE_MODULES = {
    "tushare": "data_recourses.tushare",
    "akshare": "data_recourses.akshare",
}
SOURCE_ORDER = ("tushare", "akshare")


def load_symbols(path=SYMBOLS_PATH):
    """Load symbols from either [""600000.SH""] or {""symbols"": [...]} JSON."""
    symbol_path = Path(path)
    if not symbol_path.read_text(encoding="utf-8").strip():
        return []
    with symbol_path.open(encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, dict):
        # The default symbol group is used by the data downloader.
        data = data.get("symbols", data.get("default_symbols", []))
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError("symbols.json must be a JSON string list or contain a 'symbols' string list")
    return data


def load_enabled_sources(path=CONFIG_PATH):
    with Path(path).open(encoding="utf-8") as file:
        config = json.load(file)
    sources = config.get("data_source", [])
    enabled = set()
    for item in sources:
        if not isinstance(item, dict) or not item.get("enabled"):
            continue
        name = item.get("name")
        if isinstance(name, str):
            enabled.add(name.lower())
    unknown = enabled.difference(SOURCE_MODULES)
    if unknown:
        raise ValueError(f"Unsupported data source(s): {', '.join(sorted(unknown))}")
    return [source for source in SOURCE_ORDER if source in enabled]


def download_data(start_date, end_date, symbols_path=SYMBOLS_PATH,
                  config_path=CONFIG_PATH, output_dir=OUTPUT_DIR):
    symbols = load_symbols(symbols_path)
    if not symbols:
        print("No symbols configured in data/symbols.json.")
        return {}

    result = {}
    remaining = set(symbols)
    for source in load_enabled_sources(config_path):
        if not remaining:
            break
        requested = [symbol for symbol in symbols if symbol in remaining]
        print(f"Downloading from {source}: {', '.join(requested)}")
        module = import_module(SOURCE_MODULES[source])
        try:
            paths = module.download_daily_data(requested, start_date, end_date, output_dir)
        except Exception as error:
            print(f"{source} failed: {error}")
            paths = []
        result[source] = paths

        completed = {
            Path(path).parent.name
            for path in paths
            if Path(path).parent.name in remaining
        }
        remaining.difference_update(completed)

    if remaining:
        print(f"No data downloaded for: {', '.join(symbol for symbol in symbols if symbol in remaining)}")
    return result


def _parse_args():
    # Query completed trading days by default; today's bar may not exist yet.
    end_default = date.today()
    start_default = end_default - timedelta(days=30)
    parser = argparse.ArgumentParser(description="Download daily stock data from configured sources")
    parser.add_argument("--start-date", default=start_default.strftime("%Y%m%d"), help="Start date in YYYYMMDD format")
    parser.add_argument("--end-date", default=end_default.strftime("%Y%m%d"), help="End date in YYYYMMDD format")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    download_data(arguments.start_date, arguments.end_date)
