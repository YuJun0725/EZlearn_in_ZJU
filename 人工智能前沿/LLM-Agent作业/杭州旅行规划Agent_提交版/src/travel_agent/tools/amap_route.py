from __future__ import annotations

import json
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeAlias

from travel_agent.models import POI
from travel_agent.services import (
    AmapClientError,
    AmapWebServiceClient,
    DEFAULT_ENV_PATH,
    load_amap_api_key,
)


DEFAULT_ROUTE_CACHE_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "cache"
    / "amap_routes.json"
)
AMAP_ROUTE_ENDPOINTS = {
    "walking": "https://restapi.amap.com/v5/direction/walking",
    "driving": "https://restapi.amap.com/v5/direction/driving",
}


class AmapRouteError(RuntimeError):
    """Raised when a route cannot be requested or parsed safely."""


class RouteMode(StrEnum):
    WALKING = "walking"
    DRIVING = "driving"
    TAXI = "taxi"

    @property
    def amap_mode(self) -> str:
        return "driving" if self is RouteMode.TAXI else self.value


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A longitude/latitude pair in Amap's GCJ-02 coordinate system."""

    longitude: float
    latitude: float

    def __post_init__(self) -> None:
        if not (-180 <= self.longitude <= 180):
            raise ValueError("longitude must be between -180 and 180")
        if not (-90 <= self.latitude <= 90):
            raise ValueError("latitude must be between -90 and 90")

    @classmethod
    def from_poi(cls, poi: POI) -> Coordinate:
        return cls(longitude=poi.longitude, latitude=poi.latitude)

    @property
    def amap_text(self) -> str:
        return f"{self.longitude:.6f},{self.latitude:.6f}"


CoordinateLike: TypeAlias = Coordinate | POI | tuple[float, float]


@dataclass(frozen=True, slots=True)
class RouteResult:
    origin: Coordinate
    destination: Coordinate
    mode: RouteMode
    distance_m: int
    duration_s: int
    tolls_yuan: float | None = None
    traffic_lights: int | None = None
    strategy: str | None = None
    source: str = "amap"
    fetched_at: str = ""
    from_cache: bool = False

    def __post_init__(self) -> None:
        if self.distance_m < 0:
            raise ValueError("distance_m cannot be negative")
        if self.duration_s < 0:
            raise ValueError("duration_s cannot be negative")

    @property
    def distance_km(self) -> float:
        return self.distance_m / 1000

    @property
    def duration_minutes(self) -> float:
        return self.duration_s / 60

    def to_cache_dict(self) -> dict[str, Any]:
        return {
            "origin": {
                "longitude": self.origin.longitude,
                "latitude": self.origin.latitude,
            },
            "destination": {
                "longitude": self.destination.longitude,
                "latitude": self.destination.latitude,
            },
            "mode": self.mode.value,
            "distance_m": self.distance_m,
            "duration_s": self.duration_s,
            "tolls_yuan": self.tolls_yuan,
            "traffic_lights": self.traffic_lights,
            "strategy": self.strategy,
            "source": self.source,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_cache_dict(cls, raw: Mapping[str, Any]) -> RouteResult:
        try:
            origin_raw = raw["origin"]
            destination_raw = raw["destination"]
            if not isinstance(origin_raw, Mapping) or not isinstance(
                destination_raw, Mapping
            ):
                raise ValueError("route coordinates must be objects")
            return cls(
                origin=Coordinate(
                    longitude=float(origin_raw["longitude"]),
                    latitude=float(origin_raw["latitude"]),
                ),
                destination=Coordinate(
                    longitude=float(destination_raw["longitude"]),
                    latitude=float(destination_raw["latitude"]),
                ),
                mode=RouteMode(str(raw["mode"])),
                distance_m=int(raw["distance_m"]),
                duration_s=int(raw["duration_s"]),
                tolls_yuan=_optional_float(raw.get("tolls_yuan")),
                traffic_lights=_optional_int(raw.get("traffic_lights")),
                strategy=_optional_text(raw.get("strategy")),
                source=_optional_text(raw.get("source")) or "amap",
                fetched_at=_optional_text(raw.get("fetched_at")) or "",
                from_cache=True,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AmapRouteError(f"invalid cached route record: {exc}") from exc


RouteRequester: TypeAlias = Callable[
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
    return float(raw)


def _optional_int(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    return int(float(raw))


def _positive_int(raw: Any, field_name: str) -> int:
    try:
        value = int(round(float(raw)))
    except (TypeError, ValueError) as exc:
        raise AmapRouteError(f"Amap route field '{field_name}' is invalid") from exc
    if value < 0:
        raise AmapRouteError(f"Amap route field '{field_name}' cannot be negative")
    return value


class _RouteCache:
    def __init__(self, path: Path | None) -> None:
        self._path = path.expanduser().resolve() if path is not None else None
        self._lock = threading.RLock()
        self._routes: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self._path is None or not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            routes = payload.get("routes", {})
            if not isinstance(routes, dict):
                raise ValueError("'routes' must be an object")
            self._routes = {
                str(key): dict(value)
                for key, value in routes.items()
                if isinstance(value, Mapping)
            }
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise AmapRouteError(f"Cannot load route cache {self._path}: {exc}") from exc

    def get(self, key: str, ttl_seconds: int | None) -> RouteResult | None:
        with self._lock:
            raw = self._routes.get(key)
            if raw is None:
                return None
            result = RouteResult.from_cache_dict(raw)
            if ttl_seconds is not None and self._is_expired(result, ttl_seconds):
                return None
            return result

    @staticmethod
    def _is_expired(result: RouteResult, ttl_seconds: int) -> bool:
        if not result.fetched_at:
            return True
        try:
            fetched_at = datetime.fromisoformat(result.fetched_at)
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        except ValueError:
            return True
        age_seconds = (datetime.now(timezone.utc) - fetched_at).total_seconds()
        return age_seconds > ttl_seconds

    def put(self, key: str, result: RouteResult) -> None:
        if self._path is None:
            return
        with self._lock:
            self._routes[key] = result.to_cache_dict()
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self._path.with_suffix(self._path.suffix + ".tmp")
            payload = {"version": 1, "routes": self._routes}
            temporary_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self._path)


class AmapRouteTool:
    """Request and cache walking or driving routes from Amap Web Service."""

    def __init__(
        self,
        api_key: str,
        *,
        cache_path: str | Path | None = DEFAULT_ROUTE_CACHE_PATH,
        cache_ttl_seconds: int | None = 24 * 60 * 60,
        timeout: float = 15.0,
        max_retries: int = 2,
        ca_bundle: str | Path | None = None,
        requester: RouteRequester | None = None,
    ) -> None:
        self._api_key = api_key.strip()
        if not self._api_key:
            raise ValueError("Amap API key cannot be empty")
        if cache_ttl_seconds is not None and cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds cannot be negative")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        self._cache_ttl_seconds = cache_ttl_seconds
        self._timeout = timeout
        self._max_retries = max_retries
        normalized_cache_path = Path(cache_path) if cache_path is not None else None
        self._cache = _RouteCache(normalized_cache_path)

        if requester is None:
            client = AmapWebServiceClient(
                self._api_key,
                timeout=timeout,
                max_retries=max_retries,
                ca_bundle=ca_bundle,
                user_agent="HangzhouTravelAgentRoute/1.0",
            )

            def default_requester(
                endpoint: str, params: Mapping[str, str]
            ) -> Mapping[str, Any]:
                try:
                    return client.request_json(endpoint, params)
                except AmapClientError as exc:
                    raise AmapRouteError(str(exc)) from exc

            self._requester = default_requester
        else:
            self._requester = requester

    @classmethod
    def from_env(
        cls,
        *,
        env_path: str | Path = DEFAULT_ENV_PATH,
        **kwargs: Any,
    ) -> AmapRouteTool:
        try:
            api_key = load_amap_api_key(env_path)
        except AmapClientError as exc:
            raise AmapRouteError(str(exc)) from exc
        return cls(api_key, **kwargs)

    def get_route(
        self,
        origin: CoordinateLike,
        destination: CoordinateLike,
        *,
        mode: RouteMode | str = RouteMode.WALKING,
        use_cache: bool = True,
    ) -> RouteResult:
        origin_coordinate = self._to_coordinate(origin)
        destination_coordinate = self._to_coordinate(destination)
        try:
            route_mode = mode if isinstance(mode, RouteMode) else RouteMode(mode)
        except ValueError as exc:
            supported = ", ".join(item.value for item in RouteMode)
            raise ValueError(f"unsupported route mode; use one of: {supported}") from exc

        if origin_coordinate == destination_coordinate:
            return RouteResult(
                origin=origin_coordinate,
                destination=destination_coordinate,
                mode=route_mode,
                distance_m=0,
                duration_s=0,
                source="local",
                fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )

        cache_key = self._cache_key(
            origin_coordinate, destination_coordinate, route_mode
        )
        if use_cache:
            cached = self._cache.get(cache_key, self._cache_ttl_seconds)
            if cached is not None:
                return replace(cached, mode=route_mode, from_cache=True)

        amap_mode = route_mode.amap_mode
        endpoint = AMAP_ROUTE_ENDPOINTS[amap_mode]
        payload = self._requester(
            endpoint,
            {
                "key": self._api_key,
                "origin": origin_coordinate.amap_text,
                "destination": destination_coordinate.amap_text,
                "show_fields": "cost",
            },
        )
        self._validate_api_response(payload)
        result = self._parse_route(
            payload,
            origin=origin_coordinate,
            destination=destination_coordinate,
            mode=route_mode,
        )
        self._cache.put(cache_key, result)
        return result

    def get_routes(
        self,
        pairs: Sequence[tuple[CoordinateLike, CoordinateLike]],
        *,
        mode: RouteMode | str = RouteMode.WALKING,
        use_cache: bool = True,
    ) -> tuple[RouteResult, ...]:
        return tuple(
            self.get_route(origin, destination, mode=mode, use_cache=use_cache)
            for origin, destination in pairs
        )

    @staticmethod
    def _to_coordinate(value: CoordinateLike) -> Coordinate:
        if isinstance(value, Coordinate):
            return value
        if isinstance(value, POI):
            return Coordinate.from_poi(value)
        if isinstance(value, tuple) and len(value) == 2:
            return Coordinate(longitude=float(value[0]), latitude=float(value[1]))
        raise TypeError("coordinate must be Coordinate, POI or (longitude, latitude)")

    @staticmethod
    def _cache_key(
        origin: Coordinate, destination: Coordinate, mode: RouteMode
    ) -> str:
        return f"{mode.value}|{origin.amap_text}|{destination.amap_text}"

    @staticmethod
    def _validate_api_response(payload: Mapping[str, Any]) -> None:
        if str(payload.get("status")) != "1":
            info = payload.get("info", "unknown API error")
            infocode = payload.get("infocode", "unknown")
            raise AmapRouteError(f"Amap API error {infocode}: {info}")

    @staticmethod
    def _parse_route(
        payload: Mapping[str, Any],
        *,
        origin: Coordinate,
        destination: Coordinate,
        mode: RouteMode,
    ) -> RouteResult:
        route = payload.get("route")
        if not isinstance(route, Mapping):
            raise AmapRouteError("Amap response does not contain a route object")
        paths = route.get("paths")
        if not isinstance(paths, Sequence) or isinstance(paths, (str, bytes)):
            raise AmapRouteError("Amap response does not contain route paths")

        parsed_paths: list[tuple[int, int, Mapping[str, Any], Mapping[str, Any]]] = []
        for path in paths:
            if not isinstance(path, Mapping):
                continue
            cost = path.get("cost")
            if not isinstance(cost, Mapping):
                cost = {}
            duration_raw = cost.get("duration", path.get("duration"))
            try:
                distance_m = _positive_int(path.get("distance"), "distance")
                duration_s = _positive_int(duration_raw, "duration")
            except AmapRouteError:
                continue
            parsed_paths.append((duration_s, distance_m, path, cost))

        if not parsed_paths:
            raise AmapRouteError("Amap returned no usable route path")

        duration_s, distance_m, path, cost = min(
            parsed_paths, key=lambda item: (item[0], item[1])
        )
        return RouteResult(
            origin=origin,
            destination=destination,
            mode=mode,
            distance_m=distance_m,
            duration_s=duration_s,
            tolls_yuan=_optional_float(cost.get("tolls")),
            traffic_lights=_optional_int(cost.get("traffic_lights")),
            strategy=_optional_text(path.get("strategy")),
            fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
