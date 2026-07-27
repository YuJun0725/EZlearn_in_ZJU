import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.data.poi_repository import (  # noqa: E402
    DEFAULT_POI_PATH,
    POIDataError,
    POIRepository,
)
from travel_agent.models import POIQuery  # noqa: E402


class CurrentDatasetIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = POIRepository.from_jsonl(DEFAULT_POI_PATH)

    def test_loads_current_sixty_nine_pois(self) -> None:
        self.assertEqual(len(self.repository), 69)
        self.assertEqual(self.repository.report.loaded_count, 69)
        self.assertEqual(self.repository.report.skipped_count, 0)

    def test_dataset_retains_all_twelve_categories(self) -> None:
        statistics = self.repository.statistics()
        self.assertEqual(len(statistics["categories"]), 12)
        self.assertEqual(sum(statistics["categories"].values()), 69)

    def test_queries_museums_by_category(self) -> None:
        museums = self.repository.search(
            POIQuery(categories=("museum",), limit=100)
        )
        self.assertEqual(len(museums), 6)
        self.assertTrue(all(poi.category == "museum" for poi in museums))

    def test_searches_chinese_name_and_tags(self) -> None:
        results = self.repository.search_with_scores(
            POIQuery(text="博物馆", limit=10)
        )
        self.assertTrue(results)
        self.assertGreater(results[0].score, 0)
        self.assertTrue(
            all(
                "博物馆" in result.poi.name or "博物馆" in result.poi.tags
                for result in results
            )
        )

    def test_finds_exact_name_and_id(self) -> None:
        matches = self.repository.find_by_name("南宋德寿宫遗址博物馆", exact=True)
        self.assertEqual(len(matches), 1)
        self.assertIs(self.repository.get_required(matches[0].id), matches[0])

    def test_all_reviewed_records_are_planning_ready(self) -> None:
        ready_count = len(self.repository.all(planning_ready_only=True))
        self.assertEqual(ready_count, len(self.repository))
        self.assertEqual(
            len(self.repository.search(POIQuery(text="博物馆", limit=100))),
            6,
        )


class RepositoryFailureModeTests(unittest.TestCase):
    def test_lenient_mode_skips_bad_lines_and_reports_them(self) -> None:
        valid = {
            "id": "test-1",
            "name": "测试景点",
            "category": "park",
            "district": "西湖区",
            "address": "测试地址",
            "longitude": 120.1,
            "latitude": 30.2,
        }
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pois.jsonl"
            path.write_text(
                json.dumps(valid, ensure_ascii=False) + "\n{bad json}\n",
                encoding="utf-8",
            )
            repository = POIRepository.from_jsonl(path, strict=False)

        self.assertEqual(len(repository), 1)
        self.assertEqual(repository.report.skipped_count, 1)
        self.assertEqual(repository.report.issues[0].line_number, 2)

    def test_strict_mode_rejects_bad_line(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pois.jsonl"
            path.write_text("{bad json}\n", encoding="utf-8")
            with self.assertRaises(POIDataError):
                POIRepository.from_jsonl(path, strict=True)


if __name__ == "__main__":
    unittest.main()
