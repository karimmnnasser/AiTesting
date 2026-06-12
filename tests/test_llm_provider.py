# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock, patch

from providers.llm_provider import ask_llm, extract_json


class LLMProviderTests(unittest.TestCase):
    def test_extract_json_valid_action(self):
        parsed = extract_json('{"action": "read_file", "parameters": {"path": "a.txt"}}')
        self.assertEqual(parsed, {"action": "read_file", "parameters": {"path": "a.txt"}})

    def test_extract_json_actions_list(self):
        parsed = extract_json('{"actions": [{"action": "write_file", "path": "a.txt", "content": "hello"}]}')
        self.assertEqual(
            parsed,
            {"action": "write_file", "parameters": {"path": "a.txt", "content": "hello"}},
        )

    def test_extract_json_plain_text(self):
        self.assertIsNone(extract_json("مرحبا، كيف يمكنني مساعدتك؟"))

    @patch.dict("os.environ", {"GROQ_API_KEY": "test-key"})
    @patch("providers.llm_provider.requests.post")
    def test_ask_llm_groq_retries_after_parse_failure(self, post):
        post.side_effect = [
            self._response({"choices": [{"message": {"content": "not json"}}]}),
            self._response({"choices": [{"message": {"content": '{"action": "system_info", "parameters": {}}'}}]}),
        ]

        raw, provider, parsed = ask_llm("show system info", "groq")

        self.assertEqual(provider, "groq")
        self.assertEqual(parsed, {"action": "system_info", "parameters": {}})
        self.assertEqual(post.call_count, 2)
        self.assertIn("system_info", raw)

    @patch("providers.llm_provider.requests.post")
    def test_ask_llm_ollama_retries_after_parse_failure(self, post):
        post.side_effect = [
            self._response({"message": {"content": "I can do that."}}),
            self._response({"message": {"content": '{"action": "list_files", "parameters": {"path": "."}}'}}),
        ]

        raw, provider, parsed = ask_llm("list files", "qwen3:8b")

        self.assertEqual(provider, "qwen3:8b")
        self.assertEqual(parsed, {"action": "list_files", "parameters": {"path": "."}})
        self.assertEqual(post.call_count, 2)
        self.assertIn("list_files", raw)

    @staticmethod
    def _response(payload):
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status.return_value = None
        return response


if __name__ == "__main__":
    unittest.main()
