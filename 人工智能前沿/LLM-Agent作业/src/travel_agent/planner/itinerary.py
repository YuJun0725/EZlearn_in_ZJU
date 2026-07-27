from __future__ import annotations

from collections.abc import Mapping
from datetime import date, timedelta

from travel_agent.config import AppConfig
from travel_agent.models import (
    DailyItinerary,
    ItineraryItem,
    TripPlan,
    TravelRequest,
)
from travel_agent.planner.optimizer import (
    ItineraryOptimizer,
    OptimizationResult,
    estimate_travel,
)
from travel_agent.tools import (
    AmapRouteError,
    AmapRouteTool,
    BudgetPolicy,
    BudgetTool,
    CandidatePOI,
    DailyWeather,
    RouteMode,
)


_WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _clock_minutes(value: str) -> int:
    hour_text, minute_text = value.split(":", 1)
    return int(hour_text) * 60 + int(minute_text)


def _clock_text(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class ItineraryPlanner:
    def __init__(
        self,
        config: AppConfig,
        *,
        optimizer: ItineraryOptimizer | None = None,
        budget_tool: BudgetTool | None = None,
        route_tool: AmapRouteTool | None = None,
    ) -> None:
        self.config = config
        self.optimizer = optimizer or ItineraryOptimizer(
            max_pois_per_day=config.max_pois_per_day,
            default_visit_duration_min=config.default_visit_duration_min,
        )
        self.budget_tool = budget_tool or BudgetTool(BudgetPolicy.from_config(config))
        self.route_tool = route_tool

    def create_plan(
        self,
        request: TravelRequest,
        candidates: tuple[CandidatePOI, ...],
        *,
        weather_by_date: Mapping[date, DailyWeather] | None = None,
        use_live_routes: bool = False,
    ) -> TripPlan:
        optimization = self.optimizer.optimize(request, candidates)
        daily_itineraries, additional_unassigned, planner_warnings = self._schedule(
            request,
            optimization,
            weather_by_date=weather_by_date or {},
            use_live_routes=use_live_routes,
        )
        budget = self.budget_tool.summarize(request, daily_itineraries)
        warnings = list(optimization.warnings)
        warnings.extend(planner_warnings)
        warnings.extend(budget.warnings)
        unassigned = [candidate.poi.name for candidate in optimization.unassigned]
        unassigned.extend(additional_unassigned)
        return TripPlan(
            request=request,
            days=daily_itineraries,
            budget=budget,
            unassigned_pois=tuple(dict.fromkeys(unassigned)),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def _schedule(
        self,
        request: TravelRequest,
        optimization: OptimizationResult,
        *,
        weather_by_date: Mapping[date, DailyWeather],
        use_live_routes: bool,
    ) -> tuple[tuple[DailyItinerary, ...], tuple[str, ...], tuple[str, ...]]:
        daily_results: list[DailyItinerary] = []
        unassigned: list[str] = []
        planner_warnings: list[str] = []
        day_end = _clock_minutes(request.daily_end)

        for optimized_day in optimization.days:
            trip_date = (
                request.start_date + timedelta(days=optimized_day.day_index - 1)
                if request.start_date
                else None
            )
            weather = weather_by_date.get(trip_date) if trip_date else None
            cursor = _clock_minutes(request.daily_start)
            previous = None
            items: list[ItineraryItem] = []
            day_warnings: list[str] = []

            for candidate in optimized_day.candidates:
                poi = candidate.poi
                distance_m = 0
                travel_min = 0
                mode = "walking"
                route_warning: str | None = None
                transport_estimated = False

                if previous is not None:
                    distance_m, travel_min, mode = estimate_travel(
                        previous, poi, request.transport_modes
                    )
                    transport_estimated = True
                    if use_live_routes and self.route_tool is not None:
                        try:
                            route_mode = {
                                "walking": RouteMode.WALKING,
                                "taxi": RouteMode.TAXI,
                                "driving": RouteMode.DRIVING,
                            }[mode]
                            route = self.route_tool.get_route(
                                previous, poi, mode=route_mode
                            )
                            distance_m = route.distance_m
                            travel_min = max(1, round(route.duration_minutes))
                            transport_estimated = False
                        except (AmapRouteError, KeyError) as exc:
                            route_warning = f"实时路线失败，使用直线距离估算：{exc}"

                arrival = cursor + travel_min
                duration = (
                    poi.recommended_duration_min
                    or self.config.default_visit_duration_min
                )
                estimated_fields: list[str] = []
                item_warnings: list[str] = list(candidate.data_warnings)
                if poi.recommended_duration_min is None:
                    estimated_fields.append("visit_duration_min")
                if transport_estimated and previous is not None:
                    estimated_fields.extend(
                        ["travel_from_previous_min", "travel_distance_m"]
                    )
                if route_warning:
                    item_warnings.append(route_warning)

                adjusted = self._adjust_for_opening_hours(
                    poi, trip_date, arrival, duration
                )
                if adjusted is None:
                    unassigned.append(poi.name)
                    day_warnings.append(f"{poi.name}无法满足开放时间，未排入")
                    continue
                arrival, opening_estimated = adjusted
                if opening_estimated:
                    estimated_fields.append("opening_hours")
                departure = arrival + duration
                if departure > day_end:
                    unassigned.append(poi.name)
                    day_warnings.append(f"{poi.name}超出每日结束时间，未排入")
                    continue

                ticket = self.budget_tool.estimate_ticket(
                    poi, request.travelers.total
                )
                transport = self.budget_tool.estimate_transport(
                    distance_m, mode, request.travelers.total
                )
                if ticket.estimated:
                    estimated_fields.append("ticket_cost_yuan")
                if transport.estimated:
                    estimated_fields.append("transport_cost_yuan")
                if ticket.warning:
                    item_warnings.append(ticket.warning)
                if transport.warning:
                    item_warnings.append(transport.warning)

                items.append(
                    ItineraryItem(
                        day_index=optimized_day.day_index,
                        order=len(items) + 1,
                        poi=poi,
                        arrival_time=_clock_text(arrival),
                        departure_time=_clock_text(departure),
                        visit_duration_min=duration,
                        travel_from_previous_min=travel_min,
                        travel_distance_m=distance_m,
                        transport_mode=mode,
                        ticket_cost_yuan=ticket.amount_yuan,
                        transport_cost_yuan=transport.amount_yuan,
                        estimated_fields=tuple(estimated_fields),
                        warnings=tuple(dict.fromkeys(item_warnings)),
                    )
                )
                cursor = departure
                previous = poi

            if weather and weather.indoor_recommended:
                outdoor_names = [
                    item.poi.name for item in items if item.poi.indoor is False
                ]
                if outdoor_names:
                    day_warnings.append(
                        "天气建议室内活动，但仍包含户外POI：" + "、".join(outdoor_names)
                    )

            daily_results.append(
                DailyItinerary(
                    day_index=optimized_day.day_index,
                    date=trip_date,
                    items=tuple(items),
                    weather_condition=weather.day_condition if weather else None,
                    indoor_recommended=(
                        weather.indoor_recommended if weather else None
                    ),
                    warnings=tuple(day_warnings),
                )
            )

        return (
            tuple(daily_results),
            tuple(unassigned),
            tuple(planner_warnings),
        )

    def _adjust_for_opening_hours(
        self,
        poi,
        trip_date: date | None,
        arrival: int,
        duration: int,
    ) -> tuple[int, bool] | None:
        if trip_date is None:
            return arrival, True
        weekday = _WEEKDAY_KEYS[trip_date.weekday()]
        windows = poi.opening_hours.get(weekday)
        if windows is None:
            default_open = _clock_minutes(self.config.default_opening_time)
            default_close = _clock_minutes(self.config.default_closing_time)
            adjusted = max(arrival, default_open)
            return (adjusted, True) if adjusted + duration <= default_close else None
        if not windows:
            return None
        for window in windows:
            adjusted = max(arrival, window.open_minutes)
            if adjusted + duration <= window.close_minutes:
                return adjusted, False
        return None
