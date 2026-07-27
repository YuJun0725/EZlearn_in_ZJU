from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, TypeAlias

from travel_agent.services import (
    AmapClientError,
    AmapWebServiceClient,
    DEFAULT_ENV_PATH,
    load_amap_api_key,
)


AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
HANGZHOU_ADCODE = "330100"
DEFAULT_WEATHER_CACHE_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "cache"
    / "amap_weather.json"
)

_RAIN_MARKERS = ("雨", "雷阵雨", "冰雹")
_SNOW_MARKERS = ("雪", "雨夹雪")
_SEVERE_MARKERS = (
    "暴雨",
    "大暴雨",
    "特大暴雨",
    "暴雪",
    "雷",
    "冰雹",
    "沙尘",
    "飑",
    "台风",
    "大风",
)


class AmapWeatherError(RuntimeError):
    """Raised when Amap weather data cannot be requested or parsed."""


@dataclass(frozen=True, slots=True)
class WeatherAssessment:
    is_rainy: bool
    is_snowy: bool
    is_severe: bool
    is_hot: bool
    is_cold: bool
    outdoor_suitable: bool
    indoor_recommended: bool
    tags: tuple[str, ...]
    advisories: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_rainy": self.is_rainy,
            "is_snowy": self.is_snowy,
            "is_severe": self.is_severe,
            "is_hot": self.is_hot,
            "is_cold": self.is_cold,
            "outdoor_suitable": self.outdoor_suitable,
            "indoor_recommended": self.indoor_recommended,
            "tags": list(self.tags),
            "advisories": list(self.advisories),
        }

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> WeatherAssessment:
        try:
            return cls(
                is_rainy=_required_bool(raw.get("is_rainy"), "is_rainy"),
                is_snowy=_required_bool(raw.get("is_snowy"), "is_snowy"),
                is_severe=_required_bool(raw.get("is_severe"), "is_severe"),
                is_hot=_required_bool(raw.get("is_hot"), "is_hot"),
                is_cold=_required_bool(raw.get("is_cold"), "is_cold"),
                outdoor_suitable=_required_bool(
                    raw.get("outdoor_suitable"), "outdoor_suitable"
                ),
                indoor_recommended=_required_bool(
                    raw.get("indoor_recommended"), "indoor_recommended"
                ),
                tags=_string_tuple(raw.get("tags")),
                advisories=_string_tuple(raw.get("advisories")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AmapWeatherError(f"invalid cached weather assessment: {exc}") from exc


@dataclass(frozen=True, slots=True)
class CurrentWeather:
    province: str
    city: str
    adcode: str
    condition: str
    temperature_c: float | None
    humidity_percent: float | None
    wind_direction: str | None
    wind_power: str | None
    report_time: str | None
    assessment: WeatherAssessment
    source: str = "amap"
    fetched_at: str = ""
    from_cache: bool = False

    @property
    def outdoor_suitable(self) -> bool:
        return self.assessment.outdoor_suitable

    @property
    def indoor_recommended(self) -> bool:
        return self.assessment.indoor_recommended

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "province": self.province,
            "city": self.city,
            "adcode": self.adcode,
            "condition": self.condition,
            "temperature_c": self.temperature_c,
            "humidity_percent": self.humidity_percent,
            "wind_direction": self.wind_direction,
            "wind_power": self.wind_power,
            "report_time": self.report_time,
            "assessment": self.assessment.to_dict(),
            "source": self.source,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_cache_dict(cls, raw: Mapping[str, Any]) -> CurrentWeather:
        try:
            assessment_raw = raw["assessment"]
            if not isinstance(assessment_raw, Mapping):
                raise ValueError("assessment must be an object")
            return cls(
                province=_required_text(raw.get("province"), "province"),
                city=_required_text(raw.get("city"), "city"),
                adcode=_required_text(raw.get("adcode"), "adcode"),
                condition=_required_text(raw.get("condition"), "condition"),
                temperature_c=_optional_float(raw.get("temperature_c")),
                humidity_percent=_optional_float(raw.get("humidity_percent")),
                wind_direction=_optional_text(raw.get("wind_direction")),
                wind_power=_optional_text(raw.get("wind_power")),
                report_time=_optional_text(raw.get("report_time")),
                assessment=WeatherAssessment.from_mapping(assessment_raw),
                source=_optional_text(raw.get("source")) or "amap",
                fetched_at=_optional_text(raw.get("fetched_at")) or "",
                from_cache=True,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AmapWeatherError(f"invalid cached current weather: {exc}") from exc


@dataclass(frozen=True, slots=True)
class DailyWeather:
    province: str
    city: str
    adcode: str
    date: date
    week: str | None
    day_condition: str
    night_condition: str
    day_temperature_c: float | None
    night_temperature_c: float | None
    day_wind_direction: str | None
    night_wind_direction: str | None
    day_wind_power: str | None
    night_wind_power: str | None
    report_time: str | None
    assessment: WeatherAssessment
    source: str = "amap"
    fetched_at: str = ""
    from_cache: bool = False

    @property
    def outdoor_suitable(self) -> bool:
        return self.assessment.outdoor_suitable

    @property
    def indoor_recommended(self) -> bool:
        return self.assessment.indoor_recommended

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "province": self.province,
            "city": self.city,
            "adcode": self.adcode,
            "date": self.date.isoformat(),
            "week": self.week,
            "day_condition": self.day_condition,
            "night_condition": self.night_condition,
            "day_temperature_c": self.day_temperature_c,
            "night_temperature_c": self.night_temperature_c,
            "day_wind_direction": self.day_wind_direction,
            "night_wind_direction": self.night_wind_direction,
            "day_wind_power": self.day_wind_power,
            "night_wind_power": self.night_wind_power,
            "report_time": self.report_time,
            "assessment": self.assessment.to_dict(),
            "source": self.source,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_cache_dict(cls, raw: Mapping[str, Any]) -> DailyWeather:
        try:
            assessment_raw = raw["assessment"]
            if not isinstance(assessment_raw, Mapping):
                raise ValueError("assessment must be an object")
            return cls(
                province=_required_text(raw.get("province"), "province"),
                city=_required_text(raw.get("city"), "city"),
                adcode=_required_text(raw.get("adcode"), "adcode"),
                date=date.fromisoformat(
                    _required_text(raw.get("date"), "date")
                ),
                week=_optional_text(raw.get("week")),
                day_condition=_required_text(
                    raw.get("day_condition"), "day_condition"
                ),
                night_condition=_required_text(
                    raw.get("night_condition"), "night_condition"
                ),
                day_temperature_c=_optional_float(raw.get("day_temperature_c")),
                night_temperature_c=_optional_float(
                    raw.get("night_temperature_c")
                ),
                day_wind_direction=_optional_text(raw.get("day_wind_direction")),
                night_wind_direction=_optional_text(
                    raw.get("night_wind_direction")
                ),
                day_wind_power=_optional_text(raw.get("day_wind_power")),
                night_wind_power=_optional_text(raw.get("night_wind_power")),
                report_time=_optional_text(raw.get("report_time")),
                assessment=WeatherAssessment.from_mapping(assessment_raw),
                source=_optional_text(raw.get("source")) or "amap",
                fetched_at=_optional_text(raw.get("fetched_at")) or "",
                from_cache=True,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AmapWeatherError(f"invalid cached daily weather: {exc}") from exc


WeatherRequester: TypeAlias = Callable[
    [str, Mapping[str, str]], Mapping[str, Any]
]


def _optional_text(raw: Any) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def _optional_float(raw: Any) -> float | None:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise AmapWeatherError(f"invalid numeric weather value: {raw}") from exc


def _required_bool(raw: Any, field_name: str) -> bool:
    if not isinstance(raw, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return raw


def _string_tuple(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("expected a list of strings")
    return tuple(str(value) for value in raw)


def assess_weather(
    condition: str,
    *,
    high_temperature_c: float | None = None,
    low_temperature_c: float | None = None,
) -> WeatherAssessment:
    normalized = condition.strip()
    is_rainy = any(marker in normalized for marker in _RAIN_MARKERS)
    is_snowy = any(marker in normalized for marker in _SNOW_MARKERS)
    is_severe = any(marker in normalized for marker in _SEVERE_MARKERS)
    is_hot = high_temperature_c is not None and high_temperature_c >= 35
    is_cold = low_temperature_c is not None and low_temperature_c <= 0

    tags: list[str] = []
    advisories: list[str] = []
    if "晴" in normalized:
        tags.append("clear")
    if "云" in normalized or "阴" in normalized:
        tags.append("cloudy")
    if is_rainy:
        tags.append("rain")
        advisories.append("有降雨，优先安排室内POI并预留交通缓冲时间")
    if is_snowy:
        tags.append("snow")
        advisories.append("有降雪或雨夹雪，注意路面和交通延误")
    if is_severe:
        tags.append("severe")
        advisories.append("存在较强天气风险，不建议安排常规户外行程")
    if is_hot:
        tags.append("hot")
        advisories.append("预计高温，减少午间户外活动并注意补水")
    if is_cold:
        tags.append("cold")
        advisories.append("预计低温，减少长时间户外停留")

    outdoor_suitable = not (is_rainy or is_snowy or is_severe or is_hot or is_cold)
    return WeatherAssessment(
        is_rainy=is_rainy,
        is_snowy=is_snowy,
        is_severe=is_severe,
        is_hot=is_hot,
        is_cold=is_cold,
        outdoor_suitable=outdoor_suitable,
        indoor_recommended=not outdoor_suitable,
        tags=tuple(dict.fromkeys(tags)),
        advisories=tuple(dict.fromkeys(advisories)),
    )


class _WeatherCache:
    def __init__(self, path: Path | None) -> None:
        self._path = path.expanduser().resolve() if path is not None else None
        self._lock = threading.RLock()
        self._entries: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self._path is None or not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            entries = payload.get("entries", {})
            if not isinstance(entries, dict):
                raise ValueError("'entries' must be an object")
            self._entries = {
                str(key): dict(value)
                for key, value in entries.items()
                if isinstance(value, Mapping)
            }
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise AmapWeatherError(
                f"Cannot load weather cache {self._path}: {exc}"
            ) from exc

    def get(self, key: str, ttl_seconds: int | None) -> Mapping[str, Any] | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if ttl_seconds is not None and self._is_expired(entry, ttl_seconds):
                return None
            value = entry.get("value")
            if not isinstance(value, Mapping):
                raise AmapWeatherError(f"Weather cache entry '{key}' is invalid")
            return value

    @staticmethod
    def _is_expired(entry: Mapping[str, Any], ttl_seconds: int) -> bool:
        cached_at_raw = _optional_text(entry.get("cached_at"))
        if not cached_at_raw:
            return True
        try:
            cached_at = datetime.fromisoformat(cached_at_raw)
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
        except ValueError:
            return True
        return (datetime.now(timezone.utc) - cached_at).total_seconds() > ttl_seconds

    def put(self, key: str, value: Mapping[str, Any]) -> None:
        if self._path is None:
            return
        with self._lock:
            self._entries[key] = {
                "cached_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "value": dict(value),
            }
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self._path.with_suffix(self._path.suffix + ".tmp")
            temporary_path.write_text(
                json.dumps(
                    {"version": 1, "entries": self._entries},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            temporary_path.replace(self._path)


class AmapWeatherTool:
    """Request, normalize and cache current and forecast weather from Amap."""

    def __init__(
        self,
        api_key: str,
        *,
        cache_path: str | Path | None = DEFAULT_WEATHER_CACHE_PATH,
        current_ttl_seconds: int | None = 30 * 60,
        forecast_ttl_seconds: int | None = 3 * 60 * 60,
        timeout: float = 15.0,
        max_retries: int = 2,
        ca_bundle: str | Path | None = None,
        requester: WeatherRequester | None = None,
    ) -> None:
        self._api_key = api_key.strip()
        if not self._api_key:
            raise ValueError("Amap API key cannot be empty")
        for ttl_name, ttl_value in (
            ("current_ttl_seconds", current_ttl_seconds),
            ("forecast_ttl_seconds", forecast_ttl_seconds),
        ):
            if ttl_value is not None and ttl_value < 0:
                raise ValueError(f"{ttl_name} cannot be negative")

        self._current_ttl_seconds = current_ttl_seconds
        self._forecast_ttl_seconds = forecast_ttl_seconds
        normalized_cache_path = Path(cache_path) if cache_path is not None else None
        self._cache = _WeatherCache(normalized_cache_path)

        if requester is None:
            client = AmapWebServiceClient(
                self._api_key,
                timeout=timeout,
                max_retries=max_retries,
                ca_bundle=ca_bundle,
                user_agent="HangzhouTravelAgentWeather/1.0",
            )

            def default_requester(
                endpoint: str, params: Mapping[str, str]
            ) -> Mapping[str, Any]:
                try:
                    return client.request_json(endpoint, params)
                except AmapClientError as exc:
                    raise AmapWeatherError(str(exc)) from exc

            self._requester = default_requester
        else:
            self._requester = requester

    @classmethod
    def from_env(
        cls,
        *,
        env_path: str | Path = DEFAULT_ENV_PATH,
        **kwargs: Any,
    ) -> AmapWeatherTool:
        try:
            api_key = load_amap_api_key(env_path)
        except AmapClientError as exc:
            raise AmapWeatherError(str(exc)) from exc
        return cls(api_key, **kwargs)

    def get_current(
        self,
        city: str = HANGZHOU_ADCODE,
        *,
        use_cache: bool = True,
    ) -> CurrentWeather:
        city_code = self._validate_city(city)
        cache_key = f"current|{city_code}"
        if use_cache:
            cached = self._cache.get(cache_key, self._current_ttl_seconds)
            if cached is not None:
                return CurrentWeather.from_cache_dict(cached)

        payload = self._request_weather(city_code, extensions="base")
        result = self._parse_current(payload)
        self._cache.put(cache_key, result.to_cache_dict())
        return result

    def get_forecast(
        self,
        city: str = HANGZHOU_ADCODE,
        *,
        use_cache: bool = True,
    ) -> tuple[DailyWeather, ...]:
        city_code = self._validate_city(city)
        cache_key = f"forecast|{city_code}"
        if use_cache:
            cached = self._cache.get(cache_key, self._forecast_ttl_seconds)
            if cached is not None:
                raw_days = cached.get("days")
                if not isinstance(raw_days, Sequence) or isinstance(
                    raw_days, (str, bytes)
                ):
                    raise AmapWeatherError("Cached forecast days are invalid")
                parsed_days: list[DailyWeather] = []
                for index, raw_day in enumerate(raw_days, start=1):
                    if not isinstance(raw_day, Mapping):
                        raise AmapWeatherError(
                            f"Cached forecast day {index} is not an object"
                        )
                    parsed_days.append(DailyWeather.from_cache_dict(raw_day))
                if not parsed_days:
                    raise AmapWeatherError("Cached forecast contains no days")
                return tuple(parsed_days)

        payload = self._request_weather(city_code, extensions="all")
        results = self._parse_forecast(payload)
        self._cache.put(
            cache_key,
            {"days": [result.to_cache_dict() for result in results]},
        )
        return results

    def get_for_date(
        self,
        target_date: date | str,
        city: str = HANGZHOU_ADCODE,
        *,
        use_cache: bool = True,
    ) -> DailyWeather:
        if isinstance(target_date, str):
            try:
                normalized_date = date.fromisoformat(target_date)
            except ValueError as exc:
                raise ValueError("target_date must use YYYY-MM-DD format") from exc
        elif isinstance(target_date, date):
            normalized_date = target_date
        else:
            raise TypeError("target_date must be a date or YYYY-MM-DD string")

        forecast = self.get_forecast(city, use_cache=use_cache)
        for daily_weather in forecast:
            if daily_weather.date == normalized_date:
                return daily_weather
        available = "、".join(item.date.isoformat() for item in forecast)
        raise AmapWeatherError(
            f"No Amap forecast for {normalized_date.isoformat()}; "
            f"available dates: {available or 'none'}"
        )

    @staticmethod
    def _validate_city(city: str) -> str:
        value = city.strip()
        if not value:
            raise ValueError("city adcode cannot be empty")
        return value

    def _request_weather(
        self, city: str, *, extensions: str
    ) -> Mapping[str, Any]:
        payload = self._requester(
            AMAP_WEATHER_URL,
            {
                "key": self._api_key,
                "city": city,
                "extensions": extensions,
                "output": "JSON",
            },
        )
        try:
            AmapWebServiceClient.validate_response(payload)
        except AmapClientError as exc:
            raise AmapWeatherError(str(exc)) from exc
        return payload

    @staticmethod
    def _parse_current(payload: Mapping[str, Any]) -> CurrentWeather:
        lives = payload.get("lives")
        if not isinstance(lives, Sequence) or isinstance(lives, (str, bytes)):
            raise AmapWeatherError("Amap current weather does not contain lives")
        if not lives or not isinstance(lives[0], Mapping):
            raise AmapWeatherError("Amap returned no current weather record")
        live = lives[0]

        condition = _required_text(live.get("weather"), "weather")
        temperature = _optional_float(
            live.get("temperature_float", live.get("temperature"))
        )
        assessment = assess_weather(
            condition,
            high_temperature_c=temperature,
            low_temperature_c=temperature,
        )
        return CurrentWeather(
            province=_required_text(live.get("province"), "province"),
            city=_required_text(live.get("city"), "city"),
            adcode=_required_text(live.get("adcode"), "adcode"),
            condition=condition,
            temperature_c=temperature,
            humidity_percent=_optional_float(
                live.get("humidity_float", live.get("humidity"))
            ),
            wind_direction=_optional_text(live.get("winddirection")),
            wind_power=_optional_text(live.get("windpower")),
            report_time=_optional_text(live.get("reporttime")),
            assessment=assessment,
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )

    @staticmethod
    def _parse_forecast(
        payload: Mapping[str, Any]
    ) -> tuple[DailyWeather, ...]:
        forecasts = payload.get("forecasts")
        if not isinstance(forecasts, Sequence) or isinstance(
            forecasts, (str, bytes)
        ):
            raise AmapWeatherError("Amap forecast does not contain forecasts")
        if not forecasts or not isinstance(forecasts[0], Mapping):
            raise AmapWeatherError("Amap returned no forecast record")
        forecast = forecasts[0]
        casts = forecast.get("casts")
        if not isinstance(casts, Sequence) or isinstance(casts, (str, bytes)):
            raise AmapWeatherError("Amap forecast does not contain daily casts")

        province = _required_text(forecast.get("province"), "province")
        city = _required_text(forecast.get("city"), "city")
        adcode = _required_text(forecast.get("adcode"), "adcode")
        report_time = _optional_text(forecast.get("reporttime"))
        fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        results: list[DailyWeather] = []

        for index, cast in enumerate(casts, start=1):
            if not isinstance(cast, Mapping):
                raise AmapWeatherError(f"Amap forecast day {index} is not an object")
            try:
                forecast_date = date.fromisoformat(
                    _required_text(cast.get("date"), f"casts[{index}].date")
                )
            except ValueError as exc:
                raise AmapWeatherError(
                    f"Amap forecast day {index} has an invalid date"
                ) from exc

            day_condition = _required_text(
                cast.get("dayweather"), f"casts[{index}].dayweather"
            )
            night_condition = _required_text(
                cast.get("nightweather"), f"casts[{index}].nightweather"
            )
            day_temperature = _optional_float(
                cast.get("daytemp_float", cast.get("daytemp"))
            )
            night_temperature = _optional_float(
                cast.get("nighttemp_float", cast.get("nighttemp"))
            )
            assessment = assess_weather(
                day_condition,
                high_temperature_c=day_temperature,
                low_temperature_c=night_temperature,
            )
            results.append(
                DailyWeather(
                    province=province,
                    city=city,
                    adcode=adcode,
                    date=forecast_date,
                    week=_optional_text(cast.get("week")),
                    day_condition=day_condition,
                    night_condition=night_condition,
                    day_temperature_c=day_temperature,
                    night_temperature_c=night_temperature,
                    day_wind_direction=_optional_text(cast.get("daywind")),
                    night_wind_direction=_optional_text(cast.get("nightwind")),
                    day_wind_power=_optional_text(cast.get("daypower")),
                    night_wind_power=_optional_text(cast.get("nightpower")),
                    report_time=report_time,
                    assessment=assessment,
                    fetched_at=fetched_at,
                )
            )
        if not results:
            raise AmapWeatherError("Amap returned an empty forecast")
        return tuple(sorted(results, key=lambda item: item.date))


def _required_text(raw: Any, field_name: str) -> str:
    value = _optional_text(raw)
    if value is None:
        raise AmapWeatherError(f"Amap weather field '{field_name}' is missing")
    return value
