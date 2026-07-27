from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


_TRANSPORT_LABELS = {
    "walk": "步行",
    "walking": "步行",
    "taxi": "出租车",
    "driving": "驾车",
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _money(value: Any) -> str | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.2f}元"
    return None


def _traveler_text(request: Mapping[str, Any]) -> str:
    travelers = _mapping(request.get("travelers"))
    labels = (
        ("成人", travelers.get("adults")),
        ("儿童", travelers.get("children")),
        ("老人", travelers.get("elderly")),
    )
    return "、".join(
        f"{label}{count}人"
        for label, count in labels
        if isinstance(count, int) and count > 0
    )


def _day_narrative(day: Mapping[str, Any]) -> str:
    day_index = day.get("day_index", "?")
    date_text = f"（{day['date']}）" if day.get("date") else ""
    items = [_mapping(item) for item in _sequence(day.get("items"))]
    if not items:
        return f"第{day_index}天{date_text}暂时没有可执行的景点安排。"

    names = [
        str(_mapping(item.get("poi")).get("name", "未命名景点"))
        for item in items
    ]
    start_time = items[0].get("arrival_time")
    end_time = items[-1].get("departure_time")
    time_text = ""
    if start_time and end_time:
        time_text = f"建议从{start_time}开始，预计{end_time}结束。"

    if len(names) == 1:
        route_text = f"安排游览{names[0]}。"
    else:
        route_text = f"先游览{names[0]}，随后依次前往{'、'.join(names[1:])}。"

    modes: list[str] = []
    for item in items[1:]:
        mode = _TRANSPORT_LABELS.get(
            str(item.get("transport_mode", "")),
            str(item.get("transport_mode", "")),
        )
        if mode and mode not in modes:
            modes.append(mode)
    transport_text = f"景点之间主要采用{'和'.join(modes)}。" if modes else ""
    weather_text = (
        f"当天参考天气为{day['weather_condition']}。"
        if day.get("weather_condition")
        else ""
    )
    return f"第{day_index}天{date_text}，{time_text}{route_text}{transport_text}{weather_text}"


def format_natural_language_output(payload: Mapping[str, Any]) -> str:
    """Turn the verified structured result into a concise Chinese narrative."""

    plan = _mapping(payload.get("plan"))
    if not plan:
        return ""
    request = _mapping(payload.get("request"))
    validation = _mapping(payload.get("validation"))
    budget = _mapping(plan.get("budget"))
    days = [_mapping(day) for day in _sequence(plan.get("days"))]

    intro_parts: list[str] = []
    travelers = _traveler_text(request)
    if travelers:
        intro_parts.append(f"为{travelers}")
    city = str(request.get("city", "")).strip()
    if city:
        intro_parts.append(f"规划了一份{city}行程")
    else:
        intro_parts.append("规划了一份旅行行程")
    day_count = request.get("days") or len(days)
    if day_count:
        intro_parts.append(f"，共{day_count}天")
    poi_count = plan.get("poi_count")
    if isinstance(poi_count, int):
        intro_parts.append(f"、安排{poi_count}个景点")
    total = _money(budget.get("total_yuan"))
    if total:
        intro_parts.append(f"，预计总费用为{total}")
    paragraphs = ["".join(intro_parts) + "。"]

    preferences = [str(item) for item in _sequence(request.get("preferences"))]
    must_visit = [str(item) for item in _sequence(request.get("must_visit"))]
    preference_parts: list[str] = []
    if preferences:
        preference_parts.append("行程重点围绕" + "、".join(preferences) + "展开")
    if must_visit:
        preference_parts.append("已安排必去景点" + "、".join(must_visit))
    if preference_parts:
        paragraphs.append("，并".join(preference_parts) + "。")

    paragraphs.extend(_day_narrative(day) for day in days)

    ticket = _money(budget.get("ticket_yuan"))
    transport = _money(budget.get("transport_yuan"))
    meal = _money(budget.get("meal_yuan"))
    costs = [
        text
        for text in (
            f"门票{ticket}" if ticket else "",
            f"交通{transport}" if transport else "",
            f"餐饮{meal}" if meal else "",
        )
        if text
    ]
    if costs:
        budget_text = "费用方面，" + "、".join(costs)
        remaining = _money(budget.get("remaining_yuan"))
        if remaining and budget.get("within_budget") is True:
            budget_text += f"，预计还剩{remaining}预算"
        elif remaining and budget.get("within_budget") is False:
            budget_text += f"，预计超出{remaining}预算"
        paragraphs.append(budget_text + "。")

    if validation.get("is_valid") is True:
        paragraphs.append("该行程已通过时间、预算、重复景点和必去条件等硬约束校验。")
    elif validation:
        paragraphs.append("该行程仍存在约束问题，请根据校验结果调整后再出发。")

    return "\n".join(paragraphs)

