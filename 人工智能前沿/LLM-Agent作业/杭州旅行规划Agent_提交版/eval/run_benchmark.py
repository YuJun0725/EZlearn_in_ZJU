from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.agent import TravelPlanningAgent  # noqa: E402
from travel_agent.config import AppConfig  # noqa: E402
from travel_agent.models import TravelRequest  # noqa: E402


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(len(ordered) * fraction + 0.9999) - 1))
    return ordered[index]


def benchmark(scenarios_path: Path, iterations: int) -> dict[str, Any]:
    scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    config = AppConfig.from_env()
    agent = TravelPlanningAgent.from_config(config)
    requests = [TravelRequest.from_mapping(item["request"]) for item in scenarios]

    # Warm up repository loading and Python imports before measuring repeated plans.
    agent.run(requests[0])
    durations_ms: list[float] = []
    completed = 0
    started = time.perf_counter()
    for _ in range(iterations):
        for request in requests:
            begin = time.perf_counter()
            result = agent.run(request)
            durations_ms.append((time.perf_counter() - begin) * 1000)
            completed += result.is_success
    total_seconds = time.perf_counter() - started
    return {
        "mode": "offline",
        "scenario_count": len(requests),
        "iterations": iterations,
        "runs": len(durations_ms),
        "completed_runs": completed,
        "completion_rate": round(completed / len(durations_ms), 3),
        "total_seconds": round(total_seconds, 3),
        "throughput_runs_per_second": round(len(durations_ms) / total_seconds, 2),
        "average_ms": round(statistics.mean(durations_ms), 2),
        "median_ms": round(statistics.median(durations_ms), 2),
        "p95_ms": round(percentile(durations_ms, 0.95), 2),
        "max_ms": round(max(durations_ms), 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="离线旅行规划性能基准")
    parser.add_argument("--scenarios", type=Path, default=PROJECT_ROOT / "eval" / "scenarios.json")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.iterations <= 0:
        raise SystemExit("iterations must be positive")
    report = benchmark(args.scenarios, args.iterations)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["completion_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
