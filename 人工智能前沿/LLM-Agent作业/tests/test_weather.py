import sys
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from travel_agent.tools import (  # noqa: E402
    AmapWeatherError,
    AmapWeatherTool,
    assess_weather,
)


def current_payload(condition: str = "晴") -> dict[str, Any]:
    return {
        "status": "1",
        "info": "OK",
        "infocode": "10000",
        "lives": [
            {
                "province": "浙江",
                "city": "杭州市",
                "adcode": "330100",
                "weather": condition,
                "temperature": "31",
                "winddirection": "东",
                "windpower": "≤3",
                "humidity": "65",
                "reporttime": "2026-07-25 14:00:00",
                "temperature_float": "31.0",
                "humidity_float": "65.0",
            }
        ],
    }


def forecast_payload() -> dict[str, Any]:
    return {
        "status": "1",
        "info": "OK",
        "infocode": "10000",
        "forecasts": [
            {
                "province": "浙江",
                "city": "杭州市",
                "adcode": "330100",
                "reporttime": "2026-07-25 14:00:00",
                "casts": [
                    {
                        "date": "2026-07-25",
                        "week": "6",
                        "dayweather": "晴",
                        "nightweather": "多云",
                        "daytemp": "34",
                        "nighttemp": "27",
                        "daywind": "东",
                        "nightwind": "东",
                        "daypower": "≤3",
                        "nightpower": "≤3",
                    },
                    {
                        "date": "2026-07-26",
                        "week": "7",
                        "dayweather": "雷阵雨",
                        "nightweather": "中雨",
                        "daytemp": "32",
                        "nighttemp": "25",
                        "daywind": "南",
                        "nightwind": "南",
                        "daypower": "4",
                        "nightpower": "≤3",
                    },
                ],
            }
        ],
    }


class WeatherAssessmentTests(unittest.TestCase):
    def test_clear_weather_is_outdoor_suitable(self) -> None:
        assessment = assess_weather(
            "晴", high_temperature_c=30, low_temperature_c=20
        )
        self.assertTrue(assessment.outdoor_suitable)
        self.assertFalse(assessment.indoor_recommended)

    def test_rain_recommends_indoor_pois(self) -> None:
        assessment = assess_weather(
            "雷阵雨", high_temperature_c=31, low_temperature_c=24
        )
        self.assertTrue(assessment.is_rainy)
        self.assertTrue(assessment.is_severe)
        self.assertTrue(assessment.indoor_recommended)
        self.assertIn("rain", assessment.tags)

    def test_extreme_temperature_is_not_outdoor_suitable(self) -> None:
        self.assertTrue(
            assess_weather("晴", high_temperature_c=36).indoor_recommended
        )
        self.assertTrue(
            assess_weather("晴", low_temperature_c=-1).indoor_recommended
        )


class AmapWeatherToolTests(unittest.TestCase):
    def test_parses_current_weather(self) -> None:
        seen_params: list[Mapping[str, str]] = []

        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            seen_params.append(params)
            return current_payload()

        tool = AmapWeatherTool("test-key", cache_path=None, requester=requester)
        weather = tool.get_current()

        self.assertEqual(seen_params[0]["extensions"], "base")
        self.assertEqual(seen_params[0]["city"], "330100")
        self.assertEqual(weather.city, "杭州市")
        self.assertEqual(weather.temperature_c, 31)
        self.assertTrue(weather.outdoor_suitable)

    def test_parses_forecast_and_rain_assessment(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return forecast_payload()

        tool = AmapWeatherTool("test-key", cache_path=None, requester=requester)
        forecast = tool.get_forecast()

        self.assertEqual(len(forecast), 2)
        self.assertEqual(forecast[1].date, date(2026, 7, 26))
        self.assertTrue(forecast[1].assessment.is_rainy)
        self.assertTrue(forecast[1].indoor_recommended)

    def test_gets_weather_for_specific_date(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return forecast_payload()

        tool = AmapWeatherTool("test-key", cache_path=None, requester=requester)
        weather = tool.get_for_date("2026-07-26")

        self.assertEqual(weather.day_condition, "雷阵雨")

    def test_reports_date_outside_forecast_window(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return forecast_payload()

        tool = AmapWeatherTool("test-key", cache_path=None, requester=requester)
        with self.assertRaisesRegex(AmapWeatherError, "available dates"):
            tool.get_for_date("2026-08-30")

    def test_forecast_cache_avoids_duplicate_request(self) -> None:
        call_count = 0

        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            nonlocal call_count
            call_count += 1
            return forecast_payload()

        with TemporaryDirectory() as temporary_directory:
            tool = AmapWeatherTool(
                "test-key",
                cache_path=Path(temporary_directory) / "weather.json",
                forecast_ttl_seconds=None,
                requester=requester,
            )
            first = tool.get_forecast()
            second = tool.get_forecast()

        self.assertEqual(call_count, 1)
        self.assertFalse(first[0].from_cache)
        self.assertTrue(second[0].from_cache)

    def test_api_error_preserves_infocode(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return {
                "status": "0",
                "info": "INVALID_USER_KEY",
                "infocode": "10001",
            }

        tool = AmapWeatherTool("test-key", cache_path=None, requester=requester)
        with self.assertRaisesRegex(AmapWeatherError, "10001"):
            tool.get_current()

    def test_rejects_empty_weather_response(self) -> None:
        def requester(
            endpoint: str, params: Mapping[str, str]
        ) -> Mapping[str, Any]:
            return {
                "status": "1",
                "info": "OK",
                "infocode": "10000",
                "lives": [],
            }

        tool = AmapWeatherTool("test-key", cache_path=None, requester=requester)
        with self.assertRaisesRegex(AmapWeatherError, "no current weather"):
            tool.get_current()


if __name__ == "__main__":
    unittest.main()

