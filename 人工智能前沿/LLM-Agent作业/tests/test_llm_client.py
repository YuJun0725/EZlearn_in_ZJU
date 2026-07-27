import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.llm import LLMClientError, OpenAICompatibleClient  # noqa: E402


class OpenAICompatibleClientTests(unittest.TestCase):
    def test_parses_fenced_json_into_travel_request(self) -> None:
        captured = {}

        def requester(url, headers, body, timeout):
            captured.update(
                url=url,
                authorization=headers["Authorization"],
                payload=json.loads(body.decode("utf-8")),
                timeout=timeout,
            )
            return {
                "choices": [
                    {
                        "message": {
                            "content": "```json\n"
                            '{"city":"杭州市","days":2,'
                            '"preferences":["历史"],"travelers":{"adults":2}}'
                            "\n```"
                        }
                    }
                ]
            }

        client = OpenAICompatibleClient(
            "secret", "https://example.com/v1", "test-model", requester=requester
        )
        request = client.parse_travel_request("两个人在杭州玩两天，喜欢历史")
        self.assertEqual(request.days, 2)
        self.assertEqual(request.travelers.total, 2)
        self.assertEqual(captured["url"], "https://example.com/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer secret")
        self.assertEqual(captured["payload"]["temperature"], 0)

    def test_rejects_non_json_model_response(self) -> None:
        client = OpenAICompatibleClient(
            "secret",
            "https://example.com/v1",
            "test-model",
            requester=lambda *_: {"choices": [{"message": {"content": "不是JSON"}}]},
        )
        with self.assertRaises(LLMClientError):
            client.parse_travel_request("杭州两日游")


if __name__ == "__main__":
    unittest.main()
