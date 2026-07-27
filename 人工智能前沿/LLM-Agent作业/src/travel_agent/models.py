from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any


WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_CLOCK_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})$")
_TAG_SPLIT_PATTERN = re.compile(r"[|;,，、/]")


class ModelValidationError(ValueError):
    """Raised when external data cannot be converted to a domain model."""


class WalkLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def normalize_text(value: str) -> str:
    """Normalize text for stable case-insensitive matching."""

    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"\s+", " ", normalized)


def compact_text(value: str) -> str:
    normalized = normalize_text(value)
    return re.sub(r"[\s\-_，,。.;；:：/\\()（）]+", "", normalized)


def _required_text(raw: Any, field_name: str) -> str:
    value = "" if raw is None else str(raw).strip()
    if not value:
        raise ModelValidationError(f"{field_name} is required")
    return value


def _optional_text(raw: Any) -> str | None:
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def _optional_float(raw: Any, field_name: str) -> float | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        raise ModelValidationError(f"{field_name} must be numeric")
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ModelValidationError(f"{field_name} must be numeric") from exc


def _optional_int(raw: Any, field_name: str) -> int | None:
    number = _optional_float(raw, field_name)
    if number is None:
        return None
    if not number.is_integer():
        raise ModelValidationError(f"{field_name} must be an integer")
    return int(number)


def _optional_bool(raw: Any, field_name: str) -> bool | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, bool):
        return raw
    normalized = str(raw).strip().casefold()
    if normalized in {"true", "1", "yes", "y", "是"}:
        return True
    if normalized in {"false", "0", "no", "n", "否"}:
        return False
    raise ModelValidationError(f"{field_name} must be true or false")


def _clock_to_minutes(value: str, field_name: str) -> int:
    match = _CLOCK_PATTERN.fullmatch(value.strip())
    if not match:
        raise ModelValidationError(f"{field_name} must use HH:MM format")
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour == 24 and minute == 0:
        return 24 * 60
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ModelValidationError(f"{field_name} is not a valid clock time")
    return hour * 60 + minute


def _string_tuple(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        values: Sequence[Any] = _TAG_SPLIT_PATTERN.split(raw)
    elif isinstance(raw, Sequence):
        values = raw
    else:
        raise ModelValidationError("expected a string or a list of strings")

    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        value = str(item).strip()
        normalized = normalize_text(value)
        if value and normalized not in seen:
            result.append(value)
            seen.add(normalized)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class OpeningWindow:
    open: str
    close: str

    def __post_init__(self) -> None:
        start = _clock_to_minutes(self.open, "open")
        end = _clock_to_minutes(self.close, "close")
        if start >= end:
            raise ModelValidationError("opening time must be before closing time")
        object.__setattr__(self, "open", f"{start // 60:02d}:{start % 60:02d}")
        object.__setattr__(self, "close", f"{end // 60:02d}:{end % 60:02d}")

    @property
    def open_minutes(self) -> int:
        return _clock_to_minutes(self.open, "open")

    @property
    def close_minutes(self) -> int:
        return _clock_to_minutes(self.close, "close")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> OpeningWindow:
        return cls(
            open=_required_text(value.get("open"), "opening window open"),
            close=_required_text(value.get("close"), "opening window close"),
        )

    def to_dict(self) -> dict[str, str]:
        return {"open": self.open, "close": self.close}


@dataclass(frozen=True, slots=True)
class OpeningHours:
    """Weekly opening hours. None means unknown; an empty tuple means closed."""

    weekly: Mapping[str, tuple[OpeningWindow, ...] | None] = field(
        default_factory=lambda: {weekday: None for weekday in WEEKDAYS}
    )

    def __post_init__(self) -> None:
        normalized: dict[str, tuple[OpeningWindow, ...] | None] = {}
        for weekday in WEEKDAYS:
            windows = self.weekly.get(weekday)
            normalized[weekday] = None if windows is None else tuple(windows)
        object.__setattr__(self, "weekly", normalized)

    @classmethod
    def from_mapping(cls, raw: Any) -> OpeningHours:
        if raw is None:
            return cls()
        if not isinstance(raw, Mapping):
            raise ModelValidationError("opening_hours must be an object or null")

        weekly: dict[str, tuple[OpeningWindow, ...] | None] = {}
        for weekday in WEEKDAYS:
            raw_windows = raw.get(weekday)
            if raw_windows is None:
                weekly[weekday] = None
                continue
            if not isinstance(raw_windows, Sequence) or isinstance(raw_windows, str):
                raise ModelValidationError(f"opening_hours.{weekday} must be a list")
            windows: list[OpeningWindow] = []
            for raw_window in raw_windows:
                if not isinstance(raw_window, Mapping):
                    raise ModelValidationError(
                        f"opening_hours.{weekday} contains a non-object value"
                    )
                windows.append(OpeningWindow.from_mapping(raw_window))
            weekly[weekday] = tuple(windows)
        return cls(weekly=weekly)

    def get(self, weekday: str) -> tuple[OpeningWindow, ...] | None:
        normalized = weekday.strip().casefold()
        if normalized not in WEEKDAYS:
            raise KeyError(f"unknown weekday: {weekday}")
        return self.weekly[normalized]

    def is_known(self, weekday: str) -> bool:
        return self.get(weekday) is not None

    def is_open(self, weekday: str) -> bool | None:
        windows = self.get(weekday)
        return None if windows is None else bool(windows)

    @property
    def is_complete(self) -> bool:
        return all(self.weekly[weekday] is not None for weekday in WEEKDAYS)

    def to_dict(self) -> dict[str, list[dict[str, str]] | None]:
        return {
            weekday: (
                None
                if self.weekly[weekday] is None
                else [window.to_dict() for window in self.weekly[weekday]]
            )
            for weekday in WEEKDAYS
        }


@dataclass(frozen=True, slots=True)
class POISource:
    provider: str | None = None
    poi_id: str | None = None
    retrieved_at: str | None = None

    @classmethod
    def from_mapping(cls, raw: Any) -> POISource:
        if raw is None:
            return cls()
        if not isinstance(raw, Mapping):
            raise ModelValidationError("source must be an object")
        return cls(
            provider=_optional_text(raw.get("provider")),
            poi_id=_optional_text(raw.get("poi_id")),
            retrieved_at=_optional_text(raw.get("retrieved_at")),
        )


@dataclass(frozen=True, slots=True)
class POIQuality:
    status: str = "unknown"
    issues: tuple[str, ...] = ()
    review_csv_line: int | None = None

    @classmethod
    def from_mapping(cls, raw: Any) -> POIQuality:
        if raw is None:
            return cls()
        if not isinstance(raw, Mapping):
            raise ModelValidationError("quality must be an object")
        return cls(
            status=_optional_text(raw.get("status")) or "unknown",
            issues=_string_tuple(raw.get("issues")),
            review_csv_line=_optional_int(
                raw.get("review_csv_line"), "quality.review_csv_line"
            ),
        )


@dataclass(frozen=True, slots=True)
class POI:
    id: str
    name: str
    category: str
    district: str
    address: str
    longitude: float
    latitude: float
    opening_hours: OpeningHours = field(default_factory=OpeningHours)
    opening_hours_raw: str | None = None
    ticket_price_yuan: float | None = None
    recommended_duration_min: int | None = None
    indoor: bool | None = None
    requires_reservation: bool | None = None
    walk_level: WalkLevel | None = None
    tags: tuple[str, ...] = ()
    official_url: str | None = None
    source_note: str | None = None
    planning_ready: bool = False
    quality: POIQuality = field(default_factory=POIQuality)
    source: POISource = field(default_factory=POISource)

    def __post_init__(self) -> None:
        if not (-180 <= self.longitude <= 180):
            raise ModelValidationError("longitude must be between -180 and 180")
        if not (-90 <= self.latitude <= 90):
            raise ModelValidationError("latitude must be between -90 and 90")
        if self.ticket_price_yuan is not None and self.ticket_price_yuan < 0:
            raise ModelValidationError("ticket_price_yuan cannot be negative")
        if (
            self.recommended_duration_min is not None
            and self.recommended_duration_min <= 0
        ):
            raise ModelValidationError("recommended_duration_min must be positive")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> POI:
        longitude = _optional_float(raw.get("longitude"), "longitude")
        latitude = _optional_float(raw.get("latitude"), "latitude")
        if longitude is None or latitude is None:
            raise ModelValidationError("longitude and latitude are required")

        walk_level_raw = _optional_text(raw.get("walk_level"))
        try:
            walk_level = WalkLevel(walk_level_raw) if walk_level_raw else None
        except ValueError as exc:
            raise ModelValidationError(
                "walk_level must be low, medium or high"
            ) from exc

        duration = _optional_int(
            raw.get("recommended_duration_min"), "recommended_duration_min"
        )
        planning_ready = _optional_bool(raw.get("planning_ready"), "planning_ready")

        return cls(
            id=_required_text(raw.get("id"), "id"),
            name=_required_text(raw.get("name"), "name"),
            category=_required_text(raw.get("category"), "category"),
            district=_required_text(raw.get("district"), "district"),
            address=_required_text(raw.get("address"), "address"),
            longitude=longitude,
            latitude=latitude,
            opening_hours=OpeningHours.from_mapping(raw.get("opening_hours")),
            opening_hours_raw=_optional_text(raw.get("opening_hours_raw")),
            ticket_price_yuan=_optional_float(
                raw.get("ticket_price_yuan"), "ticket_price_yuan"
            ),
            recommended_duration_min=duration,
            indoor=_optional_bool(raw.get("indoor"), "indoor"),
            requires_reservation=_optional_bool(
                raw.get("requires_reservation"), "requires_reservation"
            ),
            walk_level=walk_level,
            tags=_string_tuple(raw.get("tags")),
            official_url=_optional_text(raw.get("official_url")),
            source_note=_optional_text(raw.get("source_note")),
            planning_ready=bool(planning_ready),
            quality=POIQuality.from_mapping(raw.get("quality")),
            source=POISource.from_mapping(raw.get("source")),
        )

    @property
    def location(self) -> tuple[float, float]:
        return self.longitude, self.latitude

    @property
    def searchable_text(self) -> str:
        return " ".join(
            [self.name, self.category, self.district, self.address, *self.tags]
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "district": self.district,
            "address": self.address,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "opening_hours": self.opening_hours.to_dict(),
            "opening_hours_raw": self.opening_hours_raw,
            "ticket_price_yuan": self.ticket_price_yuan,
            "recommended_duration_min": self.recommended_duration_min,
            "indoor": self.indoor,
            "requires_reservation": self.requires_reservation,
            "walk_level": self.walk_level.value if self.walk_level else None,
            "tags": list(self.tags),
            "official_url": self.official_url,
            "planning_ready": self.planning_ready,
        }


@dataclass(frozen=True, slots=True)
class TravelerInfo:
    adults: int = 1
    children: int = 0
    elderly: int = 0

    def __post_init__(self) -> None:
        if min(self.adults, self.children, self.elderly) < 0:
            raise ModelValidationError("traveler counts cannot be negative")
        if self.total <= 0:
            raise ModelValidationError("at least one traveler is required")

    @property
    def total(self) -> int:
        return self.adults + self.children + self.elderly


@dataclass(frozen=True, slots=True)
class TravelRequest:
    city: str = "杭州市"
    days: int | None = None
    start_date: date | None = None
    travelers: TravelerInfo = field(default_factory=TravelerInfo)
    budget_yuan: float | None = None
    preferences: tuple[str, ...] = ()
    districts: tuple[str, ...] = ()
    must_visit: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    daily_start: str = "09:00"
    daily_end: str = "18:00"
    transport_modes: tuple[str, ...] = ("walk", "taxi")
    max_walk_level: WalkLevel | None = None
    indoor_preferred: bool = False
    special_requirements: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.start_date, str):
            try:
                object.__setattr__(self, "start_date", date.fromisoformat(self.start_date))
            except ValueError as exc:
                raise ModelValidationError("start_date must use YYYY-MM-DD format") from exc
        if isinstance(self.max_walk_level, str):
            try:
                object.__setattr__(
                    self, "max_walk_level", WalkLevel(self.max_walk_level)
                )
            except ValueError as exc:
                raise ModelValidationError(
                    "max_walk_level must be low, medium or high"
                ) from exc
        for field_name in (
            "preferences",
            "districts",
            "must_visit",
            "avoid",
            "transport_modes",
            "special_requirements",
            "missing_information",
        ):
            object.__setattr__(self, field_name, _string_tuple(getattr(self, field_name)))
        if self.days is not None and not (1 <= self.days <= 7):
            raise ModelValidationError("days must be between 1 and 7")
        if self.budget_yuan is not None and self.budget_yuan < 0:
            raise ModelValidationError("budget_yuan cannot be negative")
        start = _clock_to_minutes(self.daily_start, "daily_start")
        end = _clock_to_minutes(self.daily_end, "daily_end")
        if start >= end:
            raise ModelValidationError("daily_start must be before daily_end")

    @property
    def is_complete(self) -> bool:
        return self.days is not None and not self.missing_information

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> TravelRequest:
        travelers_raw = raw.get("travelers")
        if travelers_raw is None:
            travelers = TravelerInfo()
        elif isinstance(travelers_raw, Mapping):
            travelers = TravelerInfo(
                adults=int(travelers_raw.get("adults", 1)),
                children=int(travelers_raw.get("children", 0)),
                elderly=int(travelers_raw.get("elderly", 0)),
            )
        else:
            raise ModelValidationError("travelers must be an object")

        days = _optional_int(raw.get("days"), "days")
        budget = _optional_float(raw.get("budget_yuan"), "budget_yuan")
        indoor = _optional_bool(raw.get("indoor_preferred"), "indoor_preferred")
        return cls(
            city=_optional_text(raw.get("city")) or "杭州市",
            days=days,
            start_date=_optional_text(raw.get("start_date")),
            travelers=travelers,
            budget_yuan=budget,
            preferences=_string_tuple(raw.get("preferences")),
            districts=_string_tuple(raw.get("districts")),
            must_visit=_string_tuple(raw.get("must_visit")),
            avoid=_string_tuple(raw.get("avoid")),
            daily_start=_optional_text(raw.get("daily_start")) or "09:00",
            daily_end=_optional_text(raw.get("daily_end")) or "18:00",
            transport_modes=_string_tuple(raw.get("transport_modes"))
            or ("walk", "taxi"),
            max_walk_level=_optional_text(raw.get("max_walk_level")),
            indoor_preferred=bool(indoor),
            special_requirements=_string_tuple(raw.get("special_requirements")),
            missing_information=_string_tuple(raw.get("missing_information")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "city": self.city,
            "days": self.days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "travelers": {
                "adults": self.travelers.adults,
                "children": self.travelers.children,
                "elderly": self.travelers.elderly,
            },
            "budget_yuan": self.budget_yuan,
            "preferences": list(self.preferences),
            "districts": list(self.districts),
            "must_visit": list(self.must_visit),
            "avoid": list(self.avoid),
            "daily_start": self.daily_start,
            "daily_end": self.daily_end,
            "transport_modes": list(self.transport_modes),
            "max_walk_level": (
                self.max_walk_level.value if self.max_walk_level else None
            ),
            "indoor_preferred": self.indoor_preferred,
            "special_requirements": list(self.special_requirements),
            "missing_information": list(self.missing_information),
        }


@dataclass(frozen=True, slots=True)
class POIQuery:
    text: str | None = None
    categories: tuple[str, ...] = ()
    districts: tuple[str, ...] = ()
    tags_any: tuple[str, ...] = ()
    tags_all: tuple[str, ...] = ()
    indoor: bool | None = None
    requires_reservation: bool | None = None
    max_walk_level: WalkLevel | None = None
    planning_ready_only: bool = False
    include_unknown: bool = True
    limit: int = 20

    def __post_init__(self) -> None:
        if not (1 <= self.limit <= 1000):
            raise ModelValidationError("limit must be between 1 and 1000")
        for field_name in ("categories", "districts", "tags_any", "tags_all"):
            raw = getattr(self, field_name)
            object.__setattr__(self, field_name, _string_tuple(raw))
        object.__setattr__(self, "text", _optional_text(self.text))


@dataclass(frozen=True, slots=True)
class POISearchResult:
    poi: POI
    score: float
    matched_fields: tuple[str, ...] = ()


class ConstraintSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ItineraryItem:
    day_index: int
    order: int
    poi: POI
    arrival_time: str
    departure_time: str
    visit_duration_min: int
    travel_from_previous_min: int = 0
    travel_distance_m: int = 0
    transport_mode: str = "walk"
    ticket_cost_yuan: float = 0.0
    transport_cost_yuan: float = 0.0
    estimated_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.day_index < 1 or self.order < 1:
            raise ModelValidationError("day_index and order must be positive")
        arrival = _clock_to_minutes(self.arrival_time, "arrival_time")
        departure = _clock_to_minutes(self.departure_time, "departure_time")
        if arrival >= departure:
            raise ModelValidationError("arrival_time must be before departure_time")
        if self.visit_duration_min <= 0:
            raise ModelValidationError("visit_duration_min must be positive")
        if min(
            self.travel_from_previous_min,
            self.travel_distance_m,
            self.ticket_cost_yuan,
            self.transport_cost_yuan,
        ) < 0:
            raise ModelValidationError("time, distance and costs cannot be negative")
        object.__setattr__(self, "estimated_fields", _string_tuple(self.estimated_fields))
        object.__setattr__(self, "warnings", _string_tuple(self.warnings))

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_index": self.day_index,
            "order": self.order,
            "poi": self.poi.to_dict(),
            "arrival_time": self.arrival_time,
            "departure_time": self.departure_time,
            "visit_duration_min": self.visit_duration_min,
            "travel_from_previous_min": self.travel_from_previous_min,
            "travel_distance_m": self.travel_distance_m,
            "transport_mode": self.transport_mode,
            "ticket_cost_yuan": self.ticket_cost_yuan,
            "transport_cost_yuan": self.transport_cost_yuan,
            "estimated_fields": list(self.estimated_fields),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class DailyItinerary:
    day_index: int
    date: date | None
    items: tuple[ItineraryItem, ...]
    weather_condition: str | None = None
    indoor_recommended: bool | None = None
    warnings: tuple[str, ...] = ()

    @property
    def total_travel_min(self) -> int:
        return sum(item.travel_from_previous_min for item in self.items)

    @property
    def total_visit_min(self) -> int:
        return sum(item.visit_duration_min for item in self.items)

    @property
    def total_cost_yuan(self) -> float:
        return sum(
            item.ticket_cost_yuan + item.transport_cost_yuan for item in self.items
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "day_index": self.day_index,
            "date": self.date.isoformat() if self.date else None,
            "items": [item.to_dict() for item in self.items],
            "weather_condition": self.weather_condition,
            "indoor_recommended": self.indoor_recommended,
            "total_travel_min": self.total_travel_min,
            "total_visit_min": self.total_visit_min,
            "total_cost_yuan": round(self.total_cost_yuan, 2),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class BudgetSummary:
    ticket_yuan: float
    transport_yuan: float
    meal_yuan: float
    total_yuan: float
    budget_yuan: float | None
    remaining_yuan: float | None
    unknown_ticket_pois: tuple[str, ...] = ()
    estimated: bool = False
    warnings: tuple[str, ...] = ()

    @property
    def within_budget(self) -> bool | None:
        if self.budget_yuan is None:
            return None
        return self.total_yuan <= self.budget_yuan

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticket_yuan": round(self.ticket_yuan, 2),
            "transport_yuan": round(self.transport_yuan, 2),
            "meal_yuan": round(self.meal_yuan, 2),
            "total_yuan": round(self.total_yuan, 2),
            "budget_yuan": self.budget_yuan,
            "remaining_yuan": (
                round(self.remaining_yuan, 2)
                if self.remaining_yuan is not None
                else None
            ),
            "within_budget": self.within_budget,
            "unknown_ticket_pois": list(self.unknown_ticket_pois),
            "estimated": self.estimated,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class TripPlan:
    request: TravelRequest
    days: tuple[DailyItinerary, ...]
    budget: BudgetSummary
    unassigned_pois: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    @property
    def poi_count(self) -> int:
        return sum(len(day.items) for day in self.days)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "days": [day.to_dict() for day in self.days],
            "budget": self.budget.to_dict(),
            "poi_count": self.poi_count,
            "unassigned_pois": list(self.unassigned_pois),
            "warnings": list(self.warnings),
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    code: str
    severity: ConstraintSeverity
    message: str
    day_index: int | None = None
    poi_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "day_index": self.day_index,
            "poi_id": self.poi_id,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    violations: tuple[ConstraintViolation, ...] = ()

    @property
    def errors(self) -> tuple[ConstraintViolation, ...]:
        return tuple(
            item for item in self.violations if item.severity is ConstraintSeverity.ERROR
        )

    @property
    def warnings(self) -> tuple[ConstraintViolation, ...]:
        return tuple(
            item
            for item in self.violations
            if item.severity is ConstraintSeverity.WARNING
        )

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "violations": [item.to_dict() for item in self.violations],
        }


@dataclass(frozen=True, slots=True)
class ToolTrace:
    step: str
    status: str
    message: str
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "message": self.message,
            "details": dict(self.details),
        }
