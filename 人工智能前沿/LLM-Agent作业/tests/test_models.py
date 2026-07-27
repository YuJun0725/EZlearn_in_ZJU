import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.models import (  # noqa: E402
    ModelValidationError,
    OpeningHours,
    OpeningWindow,
    POI,
    TravelRequest,
    TravelerInfo,
)


class OpeningHoursModelTests(unittest.TestCase):
    def test_distinguishes_unknown_closed_and_open(self) -> None:
        hours = OpeningHours.from_mapping(
            {
                "mon": None,
                "tue": [],
                "wed": [{"open": "09:00", "close": "17:00"}],
            }
        )
        self.assertIsNone(hours.is_open("mon"))
        self.assertFalse(hours.is_open("tue"))
        self.assertTrue(hours.is_open("wed"))

    def test_rejects_invalid_window(self) -> None:
        with self.assertRaises(ModelValidationError):
            OpeningWindow(open="17:00", close="09:00")


class POIModelTests(unittest.TestCase):
    def test_loads_incomplete_poi_without_inventing_unknown_values(self) -> None:
        poi = POI.from_mapping(
            {
                "id": "test-1",
                "name": "测试景点",
                "category": "museum",
                "district": "西湖区",
                "address": "测试地址",
                "longitude": 120.1,
                "latitude": 30.2,
                "opening_hours": None,
                "ticket_price_yuan": None,
                "indoor": None,
                "requires_reservation": None,
                "planning_ready": False,
            }
        )
        self.assertIsNone(poi.ticket_price_yuan)
        self.assertIsNone(poi.indoor)
        self.assertIsNone(poi.opening_hours.is_open("mon"))
        self.assertFalse(poi.planning_ready)

    def test_rejects_missing_coordinates(self) -> None:
        with self.assertRaises(ModelValidationError):
            POI.from_mapping(
                {
                    "id": "test-1",
                    "name": "测试景点",
                    "category": "museum",
                    "district": "西湖区",
                    "address": "测试地址",
                }
            )


class TravelRequestTests(unittest.TestCase):
    def test_incomplete_request_is_allowed(self) -> None:
        request = TravelRequest(days=None)
        self.assertFalse(request.is_complete)

    def test_counts_all_travelers(self) -> None:
        travelers = TravelerInfo(adults=2, children=1, elderly=1)
        self.assertEqual(travelers.total, 4)

