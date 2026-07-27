import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.build_poi_dataset import build_record, parse_bool, parse_day_windows
from scripts.fetch_amap_pois import (
    deduplicate_pois,
    normalize_poi,
    resolve_ca_bundle,
    select_balanced_pois,
)


class OpeningHoursTests(unittest.TestCase):
    def test_parses_multiple_windows(self) -> None:
        self.assertEqual(
            parse_day_windows("09:00-12:00|13:00-17:00", "mon"),
            [
                {"open": "09:00", "close": "12:00"},
                {"open": "13:00", "close": "17:00"},
            ],
        )

    def test_parses_closed_day(self) -> None:
        self.assertEqual(parse_day_windows("closed", "mon"), [])

    def test_rejects_reversed_window(self) -> None:
        with self.assertRaises(ValueError):
            parse_day_windows("17:00-09:00", "mon")

    def test_parses_chinese_boolean(self) -> None:
        self.assertTrue(parse_bool("是", "indoor"))
        self.assertFalse(parse_bool("否", "indoor"))

    def test_invalid_walk_level_is_not_written_to_lenient_dataset(self) -> None:
        row = {
            "id": "test-1",
            "name": "测试景点",
            "category": "museum",
            "district": "上城区",
            "address": "测试地址",
            "longitude": "120.1",
            "latitude": "30.2",
            "ticket_price_yuan": "0",
            "recommended_duration_min": "90",
            "indoor": "true",
            "requires_reservation": "false",
            "walk_level": "true",
            **{
                weekday: "09:00-17:00"
                for weekday in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
            },
        }
        record, issues = build_record(row, 2)
        self.assertIsNone(record["walk_level"])
        self.assertIn("walk_level must be low, medium or high", issues)


class AmapNormalizationTests(unittest.TestCase):
    def test_deduplicates_and_merges_keywords(self) -> None:
        first = {
            "id": "B001",
            "name": "测试博物馆",
            "location": "120.1,30.2",
            "_collector": {
                "keyword": "博物馆",
                "category": "museum",
                "recommended_duration_min": 120,
                "indoor": True,
            },
        }
        second = {
            **first,
            "_collector": {
                "keyword": "展览馆",
                "category": "exhibition",
                "recommended_duration_min": 90,
                "indoor": True,
            },
        }
        records = deduplicate_pois([first, second])
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["_collector"]["keywords"], ["博物馆", "展览馆"]
        )

    def test_normalizes_business_fields_without_treating_cost_as_ticket(self) -> None:
        poi = {
            "id": "B001",
            "name": "测试博物馆",
            "location": "120.1,30.2",
            "business": {"rating": "4.8", "cost": "50"},
            "_collector": {
                "category": "museum",
                "recommended_duration_min": 120,
                "indoor": True,
                "keywords": ["博物馆"],
            },
        }
        record = normalize_poi(poi, "2026-07-25T00:00:00+00:00")
        self.assertIsNone(record["ticket_price_yuan"])
        self.assertEqual(record["amap_business_cost_yuan"], 50.0)

    def test_selects_categories_in_round_robin_order(self) -> None:
        records = [
            {"name": "museum-1", "_collector": {"category": "museum"}},
            {"name": "museum-2", "_collector": {"category": "museum"}},
            {"name": "museum-3", "_collector": {"category": "museum"}},
            {"name": "park-1", "_collector": {"category": "park"}},
            {"name": "park-2", "_collector": {"category": "park"}},
        ]
        selected = select_balanced_pois(records, 4)
        self.assertEqual(
            [record["name"] for record in selected],
            ["museum-1", "park-1", "museum-2", "park-2"],
        )

    def test_explicit_ca_bundle_must_exist(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            missing_path = Path(temporary_directory) / "missing.pem"
            with self.assertRaises(ValueError):
                resolve_ca_bundle(missing_path)

    def test_accepts_explicit_ca_bundle(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            bundle_path = Path(temporary_directory) / "ca.pem"
            bundle_path.write_text("test", encoding="ascii")
            self.assertEqual(resolve_ca_bundle(bundle_path), bundle_path.resolve())


if __name__ == "__main__":
    unittest.main()
