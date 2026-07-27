import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.agent import TravelPlanningAgent  # noqa: E402
from travel_agent.config import AppConfig  # noqa: E402
from travel_agent.data import POIRepository  # noqa: E402
from travel_agent.models import TravelRequest  # noqa: E402


class CurrentDatasetAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = AppConfig()
        cls.repository = POIRepository.from_jsonl(cls.config.poi_data_path)
        cls.agent = TravelPlanningAgent(cls.config, cls.repository)

    def test_current_69_poi_dataset_plans_end_to_end(self) -> None:
        self.assertEqual(len(self.repository), 69)
        result = self.agent.run(
            TravelRequest(
                days=2,
                preferences=("历史", "自然"),
                districts=("上城区", "西湖区"),
                must_visit=("南宋德寿宫遗址博物馆",),
                budget_yuan=1000,
            )
        )
        self.assertTrue(result.is_success)
        self.assertIsNotNone(result.plan)
        self.assertGreater(result.plan.poi_count, 0)
        self.assertTrue(result.validation.is_valid)
        self.assertIn("poi_search", [trace.step for trace in result.traces])

    def test_rejects_incomplete_request_before_tool_calls(self) -> None:
        result = self.agent.run(TravelRequest(days=None))
        self.assertFalse(result.is_success)
        self.assertEqual(result.traces[0].step, "validate_request")
        self.assertEqual(result.traces[0].status, "failed")


if __name__ == "__main__":
    unittest.main()
