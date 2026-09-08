import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MCP_DIR = Path(__file__).resolve().parent.parent / "mcp"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from tools import md_write
from tools import call_logger
from agent.agent import query_recent_stock_data


class InternalStockDataTests(unittest.TestCase):
    def test_returns_records_in_inclusive_date_range(self):
        with tempfile.TemporaryDirectory() as directory:
            stocks = Path(directory) / "stocks" / "600030.SH"
            stocks.mkdir(parents=True)
            (stocks / "20260807.json").write_text(
                json.dumps({"trade_date": "20260807", "close": 27.95}),
                encoding="utf-8",
            )
            (stocks / "20260808.json").write_text(
                json.dumps({"trade_date": "20260808", "close": 28.10}),
                encoding="utf-8",
            )
            with patch("agent.agent.STOCKS_DIR", Path(directory) / "stocks"):
                result = json.loads(query_recent_stock_data("600030.SH", "20260807"))

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["data"][0]["trade_date"], "20260807")

    def test_returns_error_for_invalid_date_range(self):
        result = json.loads(query_recent_stock_data("600030.SH", "invalid"))
        self.assertFalse(result["success"])
        self.assertIn("latest_date", result["error"])

    def test_returns_error_for_missing_stock(self):
        with patch("agent.agent.STOCKS_DIR", Path(tempfile.mkdtemp())):
            result = json.loads(query_recent_stock_data("600030.SH", "20260807"))
        self.assertFalse(result["success"])
        self.assertIn("No data directory", result["error"])


class MarkdownWriteTests(unittest.TestCase):
    def test_writes_markdown_to_requested_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reports" / "daily.md"
            result = md_write.md_write(str(path), "# Daily report\n")
            self.assertTrue(result["success"])
            self.assertEqual(path.read_text(encoding="utf-8"), "# Daily report\n")

    def test_rejects_non_markdown_path(self):
        result = md_write.md_write("report.txt", "content")
        self.assertFalse(result["success"])
        self.assertIn(".md", result["error"])


class CallLoggerTests(unittest.TestCase):
    def test_writes_one_json_record_to_daily_log(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(call_logger, "LOG_DIR", Path(directory)):
                call_logger.log_tool_call("md_write", {"file_path": "report.json"}, {"success": True})
            files = list(Path(directory).glob("*.txt"))
            self.assertEqual(len(files), 1)
            record = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertEqual(record["tool"], "md_write")
            self.assertTrue(record["result"]["success"])


if __name__ == "__main__":
    unittest.main()
