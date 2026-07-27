import sys
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.config import AppConfig  # noqa: E402
from travel_agent.models import (  # noqa: E402
    OpeningHours,
    OpeningWindow,
    POI,
    TravelRequest,
    TravelerInfo,
)
from travel_agent.planner import (  # noqa: E402
    ItineraryOptimizer,
    ItineraryPlanner,
    ItineraryValidator,
)
from travel_agent.tools import (  # noqa: E402
    BudgetPolicy,
    BudgetTool,
    CandidatePOI,
)


def make_poi(
    poi_id: str,
    name: str,
    *,
    longitude: float,
    ticket: float | None = 10.0,
    category: str = "museum",
) -> POI:
    window = (OpeningWindow("09:00", "18:00"),)
    return POI(
        id=poi_id,
        name=name,
        category=category,
        district="上城区",
        address=f"{name}地址",
        longitude=longitude,
        latitude=30.24,
        opening_hours=OpeningHours({weekday: window for weekday in (
            "mon", "tue", "wed", "thu", "fri", "sat", "sun"
        )}),
        ticket_price_yuan=ticket,
        recommended_duration_min=90,
        indoor=True,
        requires_reservation=False,
        planning_ready=True,
    )


def candidate(poi: POI, score: float, *, must: bool = False) -> CandidatePOI:
    return CandidatePOI(
        poi=poi,
        score=score,
        matched_preferences=("历史",),
        selection_reasons=("测试候选",),
        data_warnings=(),
        is_must_visit=must,
    )


class BudgetToolTests(unittest.TestCase):
    def test_uses_configured_unknown_ticket_meal_and_taxi_policy(self) -> None:
        config = AppConfig(
            unknown_ticket_estimate_yuan=25,
            meal_budget_per_person_per_day=80,
            taxi_base_fare_yuan=10,
            taxi_base_distance_km=2,
            taxi_per_km_yuan=3,
        )
        tool = BudgetTool(BudgetPolicy.from_config(config))
        poi = make_poi("p1", "未知票价", longitude=120.1, ticket=None)
        self.assertEqual(tool.estimate_ticket(poi, 2).amount_yuan, 50)
        self.assertEqual(tool.estimate_transport(4_000, "taxi", 2).amount_yuan, 16)


class OptimizerTests(unittest.TestCase):
    def test_allocates_unique_candidates_across_days(self) -> None:
        candidates = tuple(
            candidate(
                make_poi(f"p{index}", f"景点{index}", longitude=120.10 + index / 1000),
                100 - index,
            )
            for index in range(4)
        )
        request = TravelRequest(days=2, daily_start="09:00", daily_end="13:00")
        result = ItineraryOptimizer(max_pois_per_day=2).optimize(request, candidates)
        selected = [item.poi.id for day in result.days for item in day.candidates]
        self.assertEqual(len(selected), 4)
        self.assertEqual(len(set(selected)), 4)


class ItineraryPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = AppConfig(
            unknown_ticket_estimate_yuan=25,
            meal_budget_per_person_per_day=80,
            max_pois_per_day=2,
        )
        self.pois = (
            make_poi("p1", "博物馆甲", longitude=120.100, ticket=10),
            make_poi("p2", "博物馆乙", longitude=120.105, ticket=None),
        )
        self.candidates = (
            candidate(self.pois[0], 100),
            candidate(self.pois[1], 90),
        )

    def test_generates_timed_plan_and_configured_budget(self) -> None:
        request = TravelRequest(
            days=1,
            start_date=date(2026, 8, 3),
            travelers=TravelerInfo(adults=2),
            budget_yuan=500,
            preferences=("历史",),
        )
        plan = ItineraryPlanner(self.config).create_plan(request, self.candidates)
        self.assertEqual(plan.poi_count, 2)
        self.assertEqual(plan.days[0].items[0].arrival_time, "09:00")
        self.assertEqual(plan.budget.ticket_yuan, 70)
        self.assertEqual(plan.budget.meal_yuan, 160)
        self.assertTrue(plan.budget.within_budget)
        self.assertTrue(ItineraryValidator().validate(plan).is_valid)

    def test_validator_reports_missing_must_visit_and_exceeded_budget(self) -> None:
        request = TravelRequest(
            days=1,
            start_date=date(2026, 8, 3),
            budget_yuan=50,
            must_visit=("不存在的必去景点",),
        )
        plan = ItineraryPlanner(self.config).create_plan(request, self.candidates)
        report = ItineraryValidator().validate(plan)
        codes = {violation.code for violation in report.errors}
        self.assertIn("MISSING_MUST_VISIT", codes)
        self.assertIn("BUDGET_EXCEEDED", codes)


if __name__ == "__main__":
    unittest.main()

