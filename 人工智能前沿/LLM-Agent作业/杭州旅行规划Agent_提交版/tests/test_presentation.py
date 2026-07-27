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
from travel_agent.presentation import (  # noqa: E402
    format_agent_result,
    format_natural_language_output,
    format_runtime_error,
)


class CLIPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config = AppConfig()
        repository = POIRepository.from_jsonl(config.poi_data_path)
        cls.agent = TravelPlanningAgent(config, repository)

    def test_formats_successful_plan_for_human_reading(self) -> None:
        result = self.agent.run(
            TravelRequest(
                days=1,
                preferences=("历史",),
                must_visit=("南宋德寿宫遗址博物馆",),
                budget_yuan=600,
            )
        )
        rendered = format_agent_result(result)
        self.assertIn("杭州旅行规划 Agent", rendered)
        self.assertIn("每日行程", rendered)
        self.assertIn("南宋德寿宫遗址博物馆 [必去]", rendered)
        self.assertIn("费用汇总", rendered)
        self.assertIn("数据提醒", rendered)
        self.assertIn("已通过全部硬约束校验", rendered)
        self.assertIn("自然语言行程说明", rendered)
        self.assertIn("预计总费用", rendered)
        self.assertNotIn('"status":', rendered)
        self.assertNotIn("Agent执行轨迹", rendered)

        narrative = format_natural_language_output(result.to_dict())
        self.assertIn("南宋德寿宫遗址博物馆", narrative)
        self.assertIn("门票", narrative)
        self.assertIn("硬约束校验", narrative)

    def test_trace_is_optional(self) -> None:
        result = self.agent.run(TravelRequest(days=1, preferences=("自然",)))
        rendered = format_agent_result(result, show_trace=True)
        self.assertIn("Agent执行轨迹", rendered)
        self.assertIn("poi_search", rendered)

    def test_formats_runtime_error(self) -> None:
        rendered = format_runtime_error("测试错误")
        self.assertIn("运行失败", rendered)
        self.assertIn("测试错误", rendered)


if __name__ == "__main__":
    unittest.main()
