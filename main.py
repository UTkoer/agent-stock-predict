"""Command-line entry point for multi-model stock prediction."""

import argparse
import asyncio

from agent.agent import default_date_range, predict_stock


def parse_args():
    start, end = default_date_range()
    parser = argparse.ArgumentParser(description="Predict a stock using enabled LangChain models")
    parser.add_argument("stock_code", nargs="?", default=None, help="Optional stock code override")
    parser.add_argument("--start-date", default=None, help="Optional start-date override")
    parser.add_argument("--end-date", default=None, help="Optional prediction-date override")
    parser.add_argument("--model", default=None, help="Run one enabled model by name")
    return parser.parse_args()


async def async_main():
    args = parse_args()
    predictions = await predict_stock(args.stock_code, args.start_date, args.end_date, args.model)
    for model_name, prediction in predictions.items():
        print(f"\n===== {model_name} =====\n{prediction}")


if __name__ == "__main__":
    asyncio.run(async_main())
