from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
WEB_ROOT = PROJECT_ROOT / "web"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.agent import TravelPlanningAgent  # noqa: E402
from travel_agent.config import AppConfig  # noqa: E402
from travel_agent.presentation import format_natural_language_output  # noqa: E402


class TravelWebHandler(BaseHTTPRequestHandler):
    agent: TravelPlanningAgent

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {"/", "/index.html"}:
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            body = (WEB_ROOT / "index.html").read_bytes()
        except OSError as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/plan":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 256 * 1024:
                raise ValueError("请求内容为空或过大")
            raw = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("请求必须是 JSON 对象")
            text = str(raw.get("text", "")).strip()
            if not text:
                raise ValueError("请输入旅行需求")
            result = self.agent.run_text(
                text,
                use_live_weather=bool(raw.get("live_weather", False)),
                use_live_routes=bool(raw.get("live_routes", False)),
            )
            payload = result.to_dict()
            payload["natural_language_output"] = (
                format_natural_language_output(payload) or None
            )
            self._send_json(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            self._send_json({"status": "failed", "errors": [str(exc)]}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # Keep server alive for a bad upstream request.
            self._send_json(
                {"status": "failed", "errors": [str(exc)]},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="杭州旅行规划 Agent Web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = AppConfig.from_env()
    TravelWebHandler.agent = TravelPlanningAgent.from_config(
        config,
        enable_weather=True,
        enable_routes=True,
        enable_llm=True,
    )
    server = ThreadingHTTPServer((args.host, args.port), TravelWebHandler)
    print(f"Travel Agent Web UI: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
