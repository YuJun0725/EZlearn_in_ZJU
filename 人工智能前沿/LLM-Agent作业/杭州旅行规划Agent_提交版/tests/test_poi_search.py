import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.data import POIRepository  # noqa: E402
from travel_agent.models import TravelRequest, WalkLevel  # noqa: E402
from travel_agent.tools import POISearchInput, POISearchTool  # noqa: E402


class POISearchToolIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = POIRepository.from_jsonl()
        cls.tool = POISearchTool(cls.repository)

    def test_history_preference_maps_to_relevant_categories(self) -> None:
        response = self.tool.search(
            POISearchInput(preferences=("历史",), limit=12)
        )
        expected = {"museum", "historic_site", "temple", "ancient_town"}
        self.assertEqual(set(response.applied_categories), expected)
        self.assertTrue(response.candidates)
        self.assertTrue(
            all(candidate.poi.category in expected for candidate in response.candidates)
        )
        self.assertTrue(
            all("历史" in candidate.matched_preferences for candidate in response.candidates)
        )

    def test_nature_preference_maps_to_outdoor_categories(self) -> None:
        response = self.tool.search(
            POISearchInput(preferences=("自然",), limit=12)
        )
        expected = {"scenic_area", "park", "wetland"}
        self.assertEqual(set(response.applied_categories), expected)
        self.assertTrue(
            all(candidate.poi.category in expected for candidate in response.candidates)
        )

    def test_indoor_preference_boosts_indoor_candidate(self) -> None:
        response = self.tool.search(
            POISearchInput(preferences=("艺术",), indoor_preferred=True, limit=10)
        )
        self.assertTrue(response.candidates)
        self.assertTrue(response.candidates[0].poi.indoor)
        self.assertIn("适合室内游览", response.candidates[0].selection_reasons)

    def test_must_visit_is_kept_even_outside_other_filters(self) -> None:
        response = self.tool.search(
            POISearchInput(
                preferences=("自然",),
                districts=("西湖区",),
                must_visit=("南宋德寿宫遗址博物馆",),
                limit=8,
            )
        )
        candidate = response.candidates[0]
        self.assertEqual(candidate.poi.name, "南宋德寿宫遗址博物馆")
        self.assertTrue(candidate.is_must_visit)
        self.assertGreaterEqual(candidate.score, 1000)

    def test_reports_unknown_must_visit(self) -> None:
        response = self.tool.search(
            POISearchInput(must_visit=("不存在的杭州测试景点XYZ",), limit=5)
        )
        self.assertEqual(
            response.unresolved_must_visit, ("不存在的杭州测试景点XYZ",)
        )
        self.assertTrue(any("未在POI数据中找到" in item for item in response.warnings))

    def test_unmapped_and_unmatched_preference_does_not_return_random_pois(self) -> None:
        response = self.tool.search(
            POISearchInput(preferences=("不存在的偏好XYZ",), limit=5)
        )
        self.assertFalse(response.candidates)
        self.assertEqual(response.unmapped_preferences, ("不存在的偏好XYZ",))
        self.assertTrue(any("没有返回任何候选" in item for item in response.warnings))

    def test_avoid_terms_remove_matching_pois(self) -> None:
        response = self.tool.search(
            POISearchInput(preferences=("历史",), avoid=("博物馆",), limit=20)
        )
        self.assertTrue(response.candidates)
        self.assertTrue(
            all(
                "博物馆" not in candidate.poi.name
                and "博物馆" not in candidate.poi.tags
                for candidate in response.candidates
            )
        )

    def test_diversifies_categories_when_multiple_preferences_apply(self) -> None:
        response = self.tool.search(
            POISearchInput(
                preferences=("历史", "自然"),
                diversify=True,
                max_per_category=2,
                limit=12,
            )
        )
        categories = {candidate.poi.category for candidate in response.candidates}
        self.assertGreaterEqual(len(categories), 6)

    def test_reviewed_data_is_prioritized_without_warnings(self) -> None:
        response = self.tool.search(
            POISearchInput(preferences=("博物馆",), limit=3)
        )
        self.assertEqual(len(response.candidates), 3)
        for candidate in response.candidates:
            self.assertTrue(candidate.poi.planning_ready)
            self.assertFalse(candidate.data_warnings)

    def test_no_duplicate_pois_are_returned(self) -> None:
        response = self.tool.search(
            POISearchInput(
                preferences=("历史", "文化", "博物馆"),
                must_visit=("南宋德寿宫遗址博物馆",),
                limit=20,
            )
        )
        ids = [candidate.poi.id for candidate in response.candidates]
        names = [candidate.poi.name for candidate in response.candidates]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(names), len(set(names)))

    def test_builds_input_from_travel_request(self) -> None:
        request = TravelRequest(
            days=2,
            preferences=("历史",),
            must_visit=("南宋德寿宫遗址博物馆",),
            max_walk_level=WalkLevel.LOW,
        )
        criteria = POISearchInput.from_travel_request(
            request, districts=("上城区",), limit=10
        )
        self.assertEqual(criteria.preferences, ("历史",))
        self.assertEqual(criteria.max_walk_level, WalkLevel.LOW)
        self.assertEqual(criteria.districts, ("上城区",))


class POISearchInputTests(unittest.TestCase):
    def test_rejects_limit_smaller_than_must_visit_count(self) -> None:
        with self.assertRaises(ValueError):
            POISearchInput(must_visit=("A", "B"), limit=1)


if __name__ == "__main__":
    unittest.main()
