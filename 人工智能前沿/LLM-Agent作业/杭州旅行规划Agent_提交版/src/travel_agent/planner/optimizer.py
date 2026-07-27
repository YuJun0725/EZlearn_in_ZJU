from __future__ import annotations

import math
from dataclasses import dataclass

from travel_agent.models import POI, TravelRequest
from travel_agent.tools.poi_search import CandidatePOI


@dataclass(frozen=True, slots=True)
class OptimizedDay:
    day_index: int
    candidates: tuple[CandidatePOI, ...]
    estimated_minutes: int


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    days: tuple[OptimizedDay, ...]
    unassigned: tuple[CandidatePOI, ...]
    warnings: tuple[str, ...] = ()


def haversine_distance_m(origin: POI, destination: POI) -> int:
    radius_m = 6_371_000
    lat1 = math.radians(origin.latitude)
    lat2 = math.radians(destination.latitude)
    delta_lat = lat2 - lat1
    delta_lon = math.radians(destination.longitude - origin.longitude)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return int(round(2 * radius_m * math.asin(math.sqrt(value))))


def estimate_travel(
    origin: POI,
    destination: POI,
    transport_modes: tuple[str, ...],
) -> tuple[int, int, str]:
    direct_distance_m = haversine_distance_m(origin, destination)
    road_distance_m = int(round(direct_distance_m * 1.25))
    normalized_modes = {mode.strip().lower() for mode in transport_modes}
    if direct_distance_m <= 2_000 and normalized_modes.intersection(
        {"walk", "walking"}
    ):
        duration_min = max(1, math.ceil(road_distance_m / 75))
        return road_distance_m, duration_min, "walking"
    if "taxi" in normalized_modes:
        duration_min = max(5, math.ceil(road_distance_m / 420))
        return road_distance_m, duration_min, "taxi"
    if "driving" in normalized_modes:
        duration_min = max(5, math.ceil(road_distance_m / 420))
        return road_distance_m, duration_min, "driving"
    duration_min = max(1, math.ceil(road_distance_m / 75))
    return road_distance_m, duration_min, "walking"


def _clock_minutes(value: str) -> int:
    hour_text, minute_text = value.split(":", 1)
    return int(hour_text) * 60 + int(minute_text)


class ItineraryOptimizer:
    """Greedy, deterministic POI selection with time and distance penalties."""

    def __init__(
        self,
        *,
        max_pois_per_day: int = 4,
        default_visit_duration_min: int = 90,
    ) -> None:
        if max_pois_per_day <= 0 or default_visit_duration_min <= 0:
            raise ValueError("optimizer limits must be positive")
        self.max_pois_per_day = max_pois_per_day
        self.default_visit_duration_min = default_visit_duration_min

    def optimize(
        self,
        request: TravelRequest,
        candidates: tuple[CandidatePOI, ...],
    ) -> OptimizationResult:
        if request.days is None:
            raise ValueError("request.days is required for itinerary optimization")
        available_per_day = _clock_minutes(request.daily_end) - _clock_minutes(
            request.daily_start
        )
        if available_per_day <= 0:
            raise ValueError("daily time window must be positive")

        unique_candidates: list[CandidatePOI] = []
        seen_ids: set[str] = set()
        for candidate in candidates:
            if candidate.poi.id not in seen_ids:
                unique_candidates.append(candidate)
                seen_ids.add(candidate.poi.id)

        remaining = list(unique_candidates)
        optimized_days: list[OptimizedDay] = []
        warnings: list[str] = []

        for day_index in range(1, request.days + 1):
            selected: list[CandidatePOI] = []
            used_minutes = 0
            current: POI | None = None
            category_counts: dict[str, int] = {}

            while remaining and len(selected) < self.max_pois_per_day:
                feasible: list[tuple[float, int, CandidatePOI]] = []
                for candidate in remaining:
                    duration = (
                        candidate.poi.recommended_duration_min
                        or self.default_visit_duration_min
                    )
                    travel_min = 0
                    if current is not None:
                        _, travel_min, _ = estimate_travel(
                            current, candidate.poi, request.transport_modes
                        )
                    increment = duration + travel_min
                    if used_minutes + increment > available_per_day:
                        continue
                    repeat_penalty = 12 * category_counts.get(
                        candidate.poi.category, 0
                    )
                    utility = candidate.score - travel_min * 0.8 - repeat_penalty
                    feasible.append((utility, -increment, candidate))

                if not feasible:
                    break
                feasible.sort(
                    key=lambda item: (
                        -item[0],
                        -item[1],
                        item[2].poi.name,
                        item[2].poi.id,
                    )
                )
                chosen = feasible[0][2]
                duration = (
                    chosen.poi.recommended_duration_min
                    or self.default_visit_duration_min
                )
                travel_min = 0
                if current is not None:
                    _, travel_min, _ = estimate_travel(
                        current, chosen.poi, request.transport_modes
                    )
                used_minutes += duration + travel_min
                selected.append(chosen)
                remaining.remove(chosen)
                category_counts[chosen.poi.category] = (
                    category_counts.get(chosen.poi.category, 0) + 1
                )
                current = chosen.poi

            optimized_days.append(
                OptimizedDay(
                    day_index=day_index,
                    candidates=tuple(selected),
                    estimated_minutes=used_minutes,
                )
            )

        missed_must_visit = [
            candidate.poi.name for candidate in remaining if candidate.is_must_visit
        ]
        if missed_must_visit:
            warnings.append("必去景点未能排入时间窗：" + "、".join(missed_must_visit))
        if remaining:
            warnings.append(f"有{len(remaining)}个候选POI未排入最终行程")
        return OptimizationResult(
            days=tuple(optimized_days),
            unassigned=tuple(remaining),
            warnings=tuple(warnings),
        )

