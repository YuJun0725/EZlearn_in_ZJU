from __future__ import annotations

import argparse
import json
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
from travel_agent.models import TravelRequest, compact_text  # noqa: E402

from .pipeline import RAGBaseline  # noqa: E402


DEFAULT_CASES = PROJECT_ROOT / "rag_baseline" / "data" / "comparison_cases.json"


def _contains_name(requested: str, actual: str) -> bool:
    left, right = compact_text(requested), compact_text(actual)
    return bool(left and right and (left in right or right in left))


def _answer_names(answer: Any) -> list[str]:
    if not isinstance(answer, dict):
        return []
    names: list[str] = []
    for day in answer.get("days", []):
        if not isinstance(day, dict):
            continue
        for item in day.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("poi_name"), str):
                names.append(item["poi_name"])
    return names


def compare(cases_path: Path, top_k: int) -> dict[str, Any]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    rag = RAGBaseline()
    agent = TravelPlanningAgent.from_config(AppConfig.from_env())
    records: list[dict[str, Any]] = []
    for case in cases:
        request = TravelRequest.from_mapping(case["request"])
        rag_result = rag.run(case["text"], top_k=top_k, generate=True)
        retrieved_names = [item["name"] for item in rag_result["retrieved"]]
        answer_names = _answer_names(rag_result.get("answer"))
        grounded = sum(
            any(_contains_name(name, retrieved) for retrieved in retrieved_names)
            for name in answer_names
        )
        rag_answer = rag_result.get("answer") or {}
        rag_total = rag_answer.get("estimated_total_yuan") if isinstance(rag_answer, dict) else None
        rag_must_visit = sum(
            any(_contains_name(must, name) for name in answer_names)
            for must in request.must_visit
        )
        agent_started = time.perf_counter()
        # The RAG call above includes generation timing; this run measures the current local planner.
        agent_result = agent.run(request)
        agent_ms = (time.perf_counter() - agent_started) * 1000
        records.append(
            {
                "id": case["id"],
                "rag_status": rag_result["status"],
                "rag_retrieved_count": len(retrieved_names),
                "rag_answer_item_count": len(answer_names),
                "rag_grounded_rate": round(grounded / len(answer_names), 3) if answer_names else 0.0,
                "rag_must_visit_completion": round(rag_must_visit / len(request.must_visit), 3) if request.must_visit else 1.0,
                "rag_estimated_total_yuan": rag_total,
                "rag_budget_compliant": (
                    None if not isinstance(rag_total, (int, float)) or request.budget_yuan is None else rag_total <= request.budget_yuan
                ),
                "rag_generation_ms": rag_result["generation_ms"],
                "rag_errors": rag_result["errors"],
                "agent_status": agent_result.status,
                "agent_poi_count": agent_result.plan.poi_count if agent_result.plan else 0,
                "agent_constraint_satisfied": bool(agent_result.validation and agent_result.validation.is_valid),
                "agent_must_visit_completion": (
                    0.0
                    if agent_result.plan is None and request.must_visit
                    else 1.0
                    if not request.must_visit
                    else round(
                        sum(
                            any(_contains_name(must, item.poi.name) for day in agent_result.plan.days for item in day.items)
                            for must in request.must_visit
                        )
                        / len(request.must_visit),
                        3,
                    )
                ),
                "agent_budget_compliant": agent_result.plan.budget.within_budget if agent_result.plan else None,
                "agent_planning_ms": round(agent_ms, 2),
            }
        )
    successful_rag = sum(item["rag_status"] == "completed" for item in records)
    successful_agent = sum(item["agent_status"] == "completed" for item in records)
    return {
        "mode": "rag_vs_structured_agent",
        "case_count": len(records),
        "top_k": top_k,
        "rag_completion_rate": round(successful_rag / len(records), 3) if records else 0.0,
        "agent_completion_rate": round(successful_agent / len(records), 3) if records else 0.0,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="RAG 基线与结构化 Agent 对比评测")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--top-k", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare(args.cases, args.top_k)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
