import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prefill_opening_hours import parse_opening_hours_raw  # noqa: E402


class OpeningHoursPrefillTests(unittest.TestCase):
    def test_parses_same_hours_for_all_weekdays(self) -> None:
        result = parse_opening_hours_raw("周一至周日 00:00-24:00")
        self.assertEqual(set(result.weekly.values()), {"00:00-24:00"})
        self.assertEqual(result.inferred_closed, ())

    def test_infers_monday_closed_for_tuesday_to_sunday_schedule(self) -> None:
        result = parse_opening_hours_raw("周二至周日 09:30-17:00")
        self.assertEqual(result.weekly["mon"], "closed")
        self.assertEqual(result.weekly["tue"], "09:30-17:00")
        self.assertEqual(result.inferred_closed, ("mon",))

    def test_parses_different_weekday_and_weekend_hours(self) -> None:
        result = parse_opening_hours_raw(
            "周二-周五 09:00-16:00；周六-周日 09:00-16:30；周一闭馆"
        )
        self.assertEqual(result.weekly["mon"], "closed")
        self.assertEqual(result.weekly["fri"], "09:00-16:00")
        self.assertEqual(result.weekly["sat"], "09:00-16:30")

    def test_skips_conflicting_seasonal_hours(self) -> None:
        result = parse_opening_hours_raw(
            "4月至10月 周一至周日 07:30-18:30；11月至3月 周一至周日 08:00-17:30"
        )
        self.assertIsNone(result.weekly)
        self.assertIn("multiple", result.reason)

    def test_skips_multiple_venues(self) -> None:
        result = parse_opening_hours_raw(
            "杭州馆:周二至周日 09:00-17:00；安吉馆:周三至周日 09:00-17:00"
        )
        self.assertIsNone(result.weekly)
        self.assertIn("multiple venues", result.reason)


if __name__ == "__main__":
    unittest.main()
