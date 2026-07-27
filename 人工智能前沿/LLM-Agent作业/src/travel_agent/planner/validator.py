from __future__ import annotations

from travel_agent.models import (
    ConstraintSeverity,
    ConstraintViolation,
    TripPlan,
    ValidationReport,
    compact_text,
)


_WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _clock_minutes(value: str) -> int:
    hour_text, minute_text = value.split(":", 1)
    return int(hour_text) * 60 + int(minute_text)


class ItineraryValidator:
    def validate(self, plan: TripPlan) -> ValidationReport:
        violations: list[ConstraintViolation] = []
        request = plan.request

        if request.days is not None and len(plan.days) != request.days:
            violations.append(
                ConstraintViolation(
                    code="DAY_COUNT_MISMATCH",
                    severity=ConstraintSeverity.ERROR,
                    message=f"请求{request.days}天，但计划包含{len(plan.days)}天",
                )
            )

        seen_ids: set[str] = set()
        planned_names: list[str] = []
        for day in plan.days:
            previous_departure: int | None = None
            for expected_order, item in enumerate(day.items, start=1):
                arrival = _clock_minutes(item.arrival_time)
                departure = _clock_minutes(item.departure_time)
                planned_names.append(compact_text(item.poi.name))
                if item.order != expected_order:
                    violations.append(
                        ConstraintViolation(
                            code="INVALID_ORDER",
                            severity=ConstraintSeverity.ERROR,
                            message=f"{item.poi.name}的顺序编号不连续",
                            day_index=day.day_index,
                            poi_id=item.poi.id,
                        )
                    )
                if item.poi.id in seen_ids:
                    violations.append(
                        ConstraintViolation(
                            code="DUPLICATE_POI",
                            severity=ConstraintSeverity.ERROR,
                            message=f"{item.poi.name}在行程中重复出现",
                            day_index=day.day_index,
                            poi_id=item.poi.id,
                        )
                    )
                seen_ids.add(item.poi.id)
                if previous_departure is not None:
                    expected_arrival = previous_departure + item.travel_from_previous_min
                    if arrival < expected_arrival:
                        violations.append(
                            ConstraintViolation(
                                code="TIME_OVERLAP",
                                severity=ConstraintSeverity.ERROR,
                                message=f"{item.poi.name}与上一项存在时间冲突",
                                day_index=day.day_index,
                                poi_id=item.poi.id,
                            )
                        )
                if arrival < _clock_minutes(request.daily_start) or departure > _clock_minutes(
                    request.daily_end
                ):
                    violations.append(
                        ConstraintViolation(
                            code="OUTSIDE_DAILY_WINDOW",
                            severity=ConstraintSeverity.ERROR,
                            message=f"{item.poi.name}超出每日活动时间",
                            day_index=day.day_index,
                            poi_id=item.poi.id,
                        )
                    )
                previous_departure = departure

                if day.date is not None:
                    weekday = _WEEKDAY_KEYS[day.date.weekday()]
                    windows = item.poi.opening_hours.get(weekday)
                    if windows is None:
                        violations.append(
                            ConstraintViolation(
                                code="UNKNOWN_OPENING_HOURS",
                                severity=ConstraintSeverity.WARNING,
                                message=f"{item.poi.name}开放时间尚未核验",
                                day_index=day.day_index,
                                poi_id=item.poi.id,
                            )
                        )
                    elif not any(
                        arrival >= window.open_minutes
                        and departure <= window.close_minutes
                        for window in windows
                    ):
                        violations.append(
                            ConstraintViolation(
                                code="OUTSIDE_OPENING_HOURS",
                                severity=ConstraintSeverity.ERROR,
                                message=f"{item.poi.name}不在开放时间内",
                                day_index=day.day_index,
                                poi_id=item.poi.id,
                            )
                        )
                if day.indoor_recommended and item.poi.indoor is False:
                    violations.append(
                        ConstraintViolation(
                            code="WEATHER_OUTDOOR_RISK",
                            severity=ConstraintSeverity.WARNING,
                            message=f"天气不适合户外活动：{item.poi.name}",
                            day_index=day.day_index,
                            poi_id=item.poi.id,
                        )
                    )

        for must_visit in request.must_visit:
            normalized = compact_text(must_visit)
            if not any(
                normalized in planned_name or planned_name in normalized
                for planned_name in planned_names
            ):
                violations.append(
                    ConstraintViolation(
                        code="MISSING_MUST_VISIT",
                        severity=ConstraintSeverity.ERROR,
                        message=f"必去景点未排入行程：{must_visit}",
                    )
                )

        if plan.budget.within_budget is False:
            violations.append(
                ConstraintViolation(
                    code="BUDGET_EXCEEDED",
                    severity=ConstraintSeverity.ERROR,
                    message=f"预计费用{plan.budget.total_yuan:.2f}元超过预算"
                    f"{plan.budget.budget_yuan:.2f}元",
                )
            )
        if plan.budget.estimated:
            violations.append(
                ConstraintViolation(
                    code="ESTIMATED_BUDGET",
                    severity=ConstraintSeverity.WARNING,
                    message="预算包含未核验票价或交通估算",
                )
            )
        if plan.poi_count == 0:
            violations.append(
                ConstraintViolation(
                    code="EMPTY_ITINERARY",
                    severity=ConstraintSeverity.ERROR,
                    message="没有生成任何可执行景点安排",
                )
            )
        return ValidationReport(violations=tuple(violations))

