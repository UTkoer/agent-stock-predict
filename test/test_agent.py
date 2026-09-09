import unittest

from agent.agent import _parse_prediction


class ParsePredictionTests(unittest.TestCase):
    def test_parses_json_wrapped_in_reasoning_tags(self):
        raw = '<reasoning>{"prediction":"DOWN","confidence":0.62,"reasoning":"brief","report":"# Report"}</reasoning>'

        self.assertEqual(_parse_prediction(raw), ("DOWN", 0.62, "brief", "# Report"))

    def test_rejects_unrelated_json_objects(self):
        raw = 'tool result: {"success": true}\nfinal answer'

        self.assertEqual(_parse_prediction(raw), ("UNKNOWN", None, raw, ""))

    def test_recovers_a_response_missing_its_closing_brace(self):
        raw = '{"prediction":"UP","confidence":0.7,"reasoning":"brief","report":"# Report"'

        self.assertEqual(_parse_prediction(raw), ("UP", 0.7, "brief", "# Report"))
