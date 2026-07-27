from __future__ import annotations

import json
import sys
import threading
import unittest
from http.client import HTTPResponse
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from web_app import TravelWebHandler  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402


class _FakeResult:
    def to_dict(self) -> dict[str, object]:
        return {"status": "completed", "plan": {"poi_count": 1}, "errors": []}


class _FakeAgent:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool, bool]] = []

    def run_text(
        self,
        text: str,
        *,
        use_live_weather: bool = False,
        use_live_routes: bool = False,
    ) -> _FakeResult:
        self.calls.append((text, use_live_weather, use_live_routes))
        return _FakeResult()


class WebEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fake_agent = _FakeAgent()
        TravelWebHandler.agent = cls.fake_agent
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), TravelWebHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.thread.join(timeout=2)
        cls.server.server_close()

    def test_serves_html_home_page(self) -> None:
        with urlopen(self.base_url + "/", timeout=2) as response:
            body = response.read().decode("utf-8")
        self.assertEqual(response.status, 200)
        self.assertIn("杭州旅行规划", body)
        self.assertIn("/api/plan", body)

    def test_plan_endpoint_forwards_text_and_live_flags(self) -> None:
        payload = json.dumps(
            {"text": "杭州一日游", "live_weather": True, "live_routes": True},
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            self.base_url + "/api/plan",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            result = json.loads(response.read().decode("utf-8"))
        self.assertEqual(response.status, 200)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["natural_language_output"])
        self.assertEqual(self.fake_agent.calls[-1], ("杭州一日游", True, True))

    def test_plan_endpoint_rejects_empty_text(self) -> None:
        payload = b'{"text":"   "}'
        request = Request(
            self.base_url + "/api/plan",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)
        response: HTTPResponse = context.exception
        self.assertEqual(response.status, 400)
        result = json.loads(response.read().decode("utf-8"))
        self.assertIn("请输入旅行需求", result["errors"])


if __name__ == "__main__":
    unittest.main()
