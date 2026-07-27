from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.agent import TravelPlanningAgent  # noqa: E402
from travel_agent.config import AppConfig  # noqa: E402
from travel_agent.models import ModelValidationError, TravelRequest  # noqa: E402
from travel_agent.presentation import (  # noqa: E402
    format_agent_result,
    format_natural_language_output,
    format_runtime_error,
)


DEMO_REQUEST: dict[str, Any] = {
    "city": "杭州市",
    "days": 2,
    "start_date": "2026-08-01",
    "travelers": {"adults": 2, "children": 0, "elderly": 0},
    "budget_yuan": 1200,
    "preferences": ["历史", "艺术", "自然"],
    "districts": ["上城区", "西湖区"],
    "must_visit": ["南宋德寿宫遗址博物馆"],
    "avoid": ["动物园"],
    "daily_start": "09:00",
    "daily_end": "18:00",
    "transport_modes": ["walk", "taxi"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="杭州旅行规划 Agent")
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--demo", action="store_true", help="运行内置离线示例")
    input_group.add_argument("--request-json", help="结构化旅行需求 JSON 字符串")
    input_group.add_argument("--request-file", type=Path, help="旅行需求 JSON 文件")
    input_group.add_argument("--text", help="通过可选 LLM 解析自然语言需求")
    parser.add_argument("--live-weather", action="store_true", help="调用高德天气")
    parser.add_argument("--live-routes", action="store_true", help="调用高德路线")
    parser.add_argument("--json", action="store_true", help="输出完整 JSON")
    parser.add_argument("--show-trace", action="store_true", help="显示 Agent 执行轨迹")
    parser.add_argument("--output", type=Path, help="将当前格式的结果写入文件")
    return parser


def _load_request(args: argparse.Namespace) -> TravelRequest | None:
    if args.text is not None:
        return None
    if args.request_json:
        raw = json.loads(args.request_json)
    elif args.request_file:
        raw = json.loads(args.request_file.read_text(encoding="utf-8"))
    else:
        raw = DEMO_REQUEST
    if not isinstance(raw, dict):
        raise ModelValidationError("旅行需求 JSON 顶层必须是对象")
    return TravelRequest.from_mapping(raw)


def _error_payload(message: str) -> dict[str, Any]:
    return {"status": "failed", "request": None, "plan": None, "validation": None,
            "traces": [], "errors": [message]}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        request = _load_request(args)
        config = AppConfig.from_env()
        agent = TravelPlanningAgent.from_config(
            config,
            enable_weather=args.live_weather,
            enable_routes=args.live_routes,
            enable_llm=args.text is not None,
        )
        if args.text is not None:
            result = agent.run_text(
                args.text,
                use_live_weather=args.live_weather,
                use_live_routes=args.live_routes,
            )
        else:
            assert request is not None
            result = agent.run(
                request,
                use_live_weather=args.live_weather,
                use_live_routes=args.live_routes,
            )
        payload = result.to_dict()
        payload["natural_language_output"] = (
            format_natural_language_output(payload) or None
        )
        rendered = (
            json.dumps(payload, ensure_ascii=False, indent=2)
            if args.json
            else format_agent_result(result, show_trace=args.show_trace)
        )
        exit_code = 0 if result.is_success else 1
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        payload = _error_payload(str(exc))
        rendered = (
            json.dumps(payload, ensure_ascii=False, indent=2)
            if args.json
            else format_runtime_error(str(exc))
        )
        exit_code = 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
