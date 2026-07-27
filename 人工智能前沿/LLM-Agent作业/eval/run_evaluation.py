from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.agent import TravelPlanningAgent  # noqa: E402
from travel_agent.config import AppConfig  # noqa: E402
from travel_agent.models import TravelRequest, compact_text  # noqa: E402


def _must_visit_completion(request: TravelRequest, result: Any) -> float:
    if not request.must_visit:
        return 1.0
    if result.plan is None:
        return 0.0
    planned = [
        compact_text(item.poi.name)
        for day in result.plan.days
        for item in day.items
    ]
    completed = sum(
        any(
            compact_text(name) in planned_name or planned_name in compact_text(name)
            for planned_name in planned
        )
        for name in request.must_visit
    )
    return completed / len(request.must_visit)


def evaluate(scenarios_path: Path) -> dict[str, Any]:
    scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    if not isinstance(scenarios, list):
        raise ValueError("scenarios.json 顶层必须是数组")
    config = AppConfig.from_env()
    agent = TravelPlanningAgent.from_config(config)
    records: list[dict[str, Any]] = []
    for scenario in scenarios:
        request = TravelRequest.from_mapping(scenario["request"])
        result = agent.run(request)
        validation = result.validation
        plan = result.plan
        records.append(
            {
                "id": scenario["id"],
                "status": result.status,
                "constraint_satisfied": bool(validation and validation.is_valid),
                "must_visit_completion": round(
                    _must_visit_completion(request, result), 3
                ),
                "budget_compliant": (
                    None
                    if plan is None or plan.budget.within_budget is None
                    else plan.budget.within_budget
                ),
                "estimated_total_yuan": (
                    None if plan is None else round(plan.budget.total_yuan, 2)
                ),
                "poi_count": 0 if plan is None else plan.poi_count,
                "warning_count": 0 if validation is None else len(validation.warnings),
                "error_count": 0 if validation is None else len(validation.errors),
                "errors": list(result.errors),
            }
        )
    count = len(records)
    completed = sum(record["status"] == "completed" for record in records)
    return {
        "mode": "offline",
        "scenario_count": count,
        "completion_rate": round(completed / count, 3) if count else 0.0,
        "constraint_satisfaction_rate": (
            round(
                sum(record["constraint_satisfied"] for record in records) / count,
                3,
            )
            if count
            else 0.0
        ),
        "average_must_visit_completion": (
            round(sum(record["must_visit_completion"] for record in records) / count, 3)
            if count
            else 0.0
        ),
        "scenarios": records,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="离线评测旅行规划 Agent")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=PROJECT_ROOT / "eval" / "scenarios.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = evaluate(args.scenarios)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["completion_rate"] == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
