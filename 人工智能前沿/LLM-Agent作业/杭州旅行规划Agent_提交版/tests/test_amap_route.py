import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.tools import (  # noqa: E402
    AmapRouteError,
    AmapRouteTool,
    Coordinate,
    RouteMode,
)


def route_payload(
    *,
    distance: str = "1500",
    duration: str = "1200",
) -> dict[str, Any]:
    return {
        "status": "1",
        "info": "OK",
        "infocode": "10000",
        "route": {
            "paths": [
                {
                    "distance": distance,
                    "cost": {
                        "duration": duration,
                        "tolls": "0",
                        "traffic_lights": "3",
                    },
                    "strategy": "推荐路线",
                }
            ]
        },
    }


class AmapRouteToolTests(unittest.TestCase):
    def test_parses_walking_route(self) -> None:
        calls: list[tuple[str, Mapping[str, str]]] = []

        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            calls.append((endpoint, params))
            return route_payload()

        tool = AmapRouteTool("test-key", cache_path=None, requester=requester)
        result = tool.get_route(
            (120.1, 30.2),
            (120.2, 30.3),
            mode=RouteMode.WALKING,
        )

        self.assertTrue(calls[0][0].endswith("/walking"))
        self.assertEqual(calls[0][1]["origin"], "120.100000,30.200000")
        self.assertEqual(result.distance_m, 1500)
        self.assertEqual(result.duration_s, 1200)
        self.assertEqual(result.duration_minutes, 20)
        self.assertFalse(result.from_cache)

    def test_taxi_uses_driving_endpoint(self) -> None:
        endpoints: list[str] = []

        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            endpoints.append(endpoint)
            return route_payload()

        tool = AmapRouteTool("test-key", cache_path=None, requester=requester)
        result = tool.get_route(
            (120.1, 30.2), (120.2, 30.3), mode=RouteMode.TAXI
        )

        self.assertTrue(endpoints[0].endswith("/driving"))
        self.assertEqual(result.mode, RouteMode.TAXI)

    def test_cache_avoids_duplicate_request(self) -> None:
        call_count = 0

        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            nonlocal call_count
            call_count += 1
            return route_payload()

        with TemporaryDirectory() as temporary_directory:
            cache_path = Path(temporary_directory) / "routes.json"
            tool = AmapRouteTool(
                "test-key",
                cache_path=cache_path,
                cache_ttl_seconds=None,
                requester=requester,
            )
            first = tool.get_route((120.1, 30.2), (120.2, 30.3))
            second = tool.get_route((120.1, 30.2), (120.2, 30.3))

            cache_payload = json.loads(cache_path.read_text(encoding="utf-8"))

        self.assertEqual(call_count, 1)
        self.assertFalse(first.from_cache)
        self.assertTrue(second.from_cache)
        self.assertEqual(second.distance_m, first.distance_m)
        self.assertEqual(len(cache_payload["routes"]), 1)

    def test_zero_distance_does_not_call_api(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            self.fail("requester should not be called for identical coordinates")

        tool = AmapRouteTool("test-key", cache_path=None, requester=requester)
        result = tool.get_route((120.1, 30.2), (120.1, 30.2))

        self.assertEqual(result.distance_m, 0)
        self.assertEqual(result.duration_s, 0)
        self.assertEqual(result.source, "local")

    def test_selects_fastest_valid_path(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            payload = route_payload(distance="2000", duration="1500")
            payload["route"]["paths"].append(
                {"distance": "2300", "cost": {"duration": "900"}}
            )
            return payload

        tool = AmapRouteTool("test-key", cache_path=None, requester=requester)
        result = tool.get_route((120.1, 30.2), (120.2, 30.3))

        self.assertEqual(result.distance_m, 2300)
        self.assertEqual(result.duration_s, 900)

    def test_api_error_preserves_infocode(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return {
                "status": "0",
                "info": "INVALID_USER_KEY",
                "infocode": "10001",
            }

        tool = AmapRouteTool("test-key", cache_path=None, requester=requester)
        with self.assertRaisesRegex(AmapRouteError, "10001"):
            tool.get_route((120.1, 30.2), (120.2, 30.3))

    def test_rejects_response_without_route(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return {"status": "1", "info": "OK", "infocode": "10000"}

        tool = AmapRouteTool("test-key", cache_path=None, requester=requester)
        with self.assertRaisesRegex(AmapRouteError, "route object"):
            tool.get_route((120.1, 30.2), (120.2, 30.3))

    def test_coordinate_validation(self) -> None:
        with self.assertRaises(ValueError):
            Coordinate(longitude=200, latitude=30)

    def test_rejects_empty_key(self) -> None:
        with self.assertRaises(ValueError):
            AmapRouteTool("", cache_path=None)


if __name__ == "__main__":
    unittest.main()

