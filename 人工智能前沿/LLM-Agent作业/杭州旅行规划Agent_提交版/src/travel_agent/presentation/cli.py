from __future__ import annotations

from travel_agent.agent.graph import AgentResult
from travel_agent.models import ItineraryItem, TravelRequest, compact_text

from .narrative import format_natural_language_output


_CATEGORY_LABELS = {
    "museum": "博物馆",
    "art_gallery": "美术馆",
    "exhibition": "展览馆",
    "historic_site": "历史遗址",
    "temple": "寺庙",
    "ancient_town": "古镇",
    "scenic_area": "风景名胜",
    "park": "公园",
    "wetland": "湿地",
    "cultural_district": "文化街区",
    "pedestrian_street": "步行街",
    "zoo": "动物园",
}
_TRANSPORT_LABELS = {
    "walk": "步行",
    "walking": "步行",
    "taxi": "出租车",
    "driving": "驾车",
}
_TRACE_STATUS_LABELS = {
    "completed": "完成",
    "failed": "失败",
    "skipped": "跳过",
    "degraded": "降级",
    "partial": "部分完成",
    "started": "执行中",
}


def _money(value: float) -> str:
    return f"{value:.2f}元"


def _distance(distance_m: int) -> str:
    if distance_m >= 1000:
        return f"{distance_m / 1000:.2f}公里"
    return f"{distance_m}米"


def _traveler_text(request: TravelRequest) -> str:
    parts: list[str] = []
    if request.travelers.adults:
        parts.append(f"成人{request.travelers.adults}人")
    if request.travelers.children:
        parts.append(f"儿童{request.travelers.children}人")
    if request.travelers.elderly:
        parts.append(f"老人{request.travelers.elderly}人")
    return "、".join(parts)


def _is_must_visit(item: ItineraryItem, request: TravelRequest) -> bool:
    poi_name = compact_text(item.poi.name)
    return any(
        compact_text(name) in poi_name or poi_name in compact_text(name)
        for name in request.must_visit
    )


def _format_request(request: TravelRequest) -> list[str]:
    lines = [
        "旅行需求",
        f"  目的地：{request.city}",
        f"  天数：{request.days if request.days is not None else '未提供'}天",
        f"  出发日期：{request.start_date.isoformat() if request.start_date else '未指定'}",
        f"  出行人员：{_traveler_text(request)}",
        f"  预算：{_money(request.budget_yuan) if request.budget_yuan is not None else '未设置'}",
    ]
    if request.preferences:
        lines.append("  偏好：" + "、".join(request.preferences))
    if request.must_visit:
        lines.append("  必去：" + "、".join(request.must_visit))
    if request.avoid:
        lines.append("  避开：" + "、".join(request.avoid))
    return lines


def _format_itinerary(result: AgentResult) -> list[str]:
    assert result.plan is not None and result.request is not None
    lines = ["每日行程"]
    for day in result.plan.days:
        date_text = day.date.isoformat() if day.date else "日期未指定"
        weather = f" | 天气：{day.weather_condition}" if day.weather_condition else ""
        lines.append(f"  第{day.day_index}天  {date_text}{weather}")
        if not day.items:
            lines.append("    暂无可执行安排")
            continue
        for item in day.items:
            must_visit = " [必去]" if _is_must_visit(item, result.request) else ""
            lines.append(
                f"    {item.order}. {item.arrival_time}-{item.departure_time}  "
                f"{item.poi.name}{must_visit}"
            )
            category = _CATEGORY_LABELS.get(item.poi.category, item.poi.category)
            lines.append(f"       {item.poi.district} | {category} | {item.poi.address}")
            if item.order > 1:
                mode = _TRANSPORT_LABELS.get(item.transport_mode, item.transport_mode)
                lines.append(
                    f"       从上一站：{mode}{item.travel_from_previous_min}分钟，"
                    f"{_distance(item.travel_distance_m)}"
                )
            lines.append(
                f"       费用：门票{_money(item.ticket_cost_yuan)}，"
                f"交通{_money(item.transport_cost_yuan)}"
            )
        lines.append(
            f"    当日合计：游览{day.total_visit_min}分钟，"
            f"交通{day.total_travel_min}分钟，景点及交通{_money(day.total_cost_yuan)}"
        )
    return lines


def _format_budget(result: AgentResult) -> list[str]:
    assert result.plan is not None
    budget = result.plan.budget
    ticket_note = (
        f"（{len(budget.unknown_ticket_pois)}个POI票价未核验）"
        if budget.unknown_ticket_pois
        else ""
    )
    lines = [
        "费用汇总",
        f"  门票：{_money(budget.ticket_yuan)}{ticket_note}",
        f"  交通：{_money(budget.transport_yuan)}",
        f"  餐饮：{_money(budget.meal_yuan)}",
        f"  预计总计：{_money(budget.total_yuan)}",
    ]
    if budget.budget_yuan is not None:
        lines.append(f"  总预算：{_money(budget.budget_yuan)}")
        if budget.remaining_yuan is not None:
            label = "预算余额" if budget.remaining_yuan >= 0 else "超出预算"
            lines.append(f"  {label}：{_money(abs(budget.remaining_yuan))}")
    return lines


def _format_data_notices(result: AgentResult) -> list[str]:
    if result.plan is None:
        return []
    items = [item for day in result.plan.days for item in day.items]
    opening_unknown = sum("opening_hours" in item.estimated_fields for item in items)
    ticket_unknown = sum("ticket_cost_yuan" in item.estimated_fields for item in items)
    reservation_unknown = sum(item.poi.requires_reservation is None for item in items)
    walk_unknown = sum(item.poi.walk_level is None for item in items)
    transport_estimated = sum(
        "transport_cost_yuan" in item.estimated_fields for item in items
    )
    notices: list[str] = []
    if opening_unknown:
        notices.append(f"{opening_unknown}个POI开放时间未核验，本次使用默认时间窗")
    if ticket_unknown:
        notices.append(f"{ticket_unknown}个POI门票未知，本次使用开发阶段估算值")
    if reservation_unknown:
        notices.append(f"{reservation_unknown}个POI预约要求未知，出发前需再次确认")
    if walk_unknown:
        notices.append(f"{walk_unknown}个POI步行强度未知")
    if transport_estimated:
        notices.append(f"{transport_estimated}段交通费用为估算值")
    if result.plan.unassigned_pois:
        notices.append(f"另有{len(result.plan.unassigned_pois)}个候选POI未排入行程")
    if not notices:
        return []
    return ["数据提醒", *(f"  - {notice}" for notice in notices)]


def _format_validation(result: AgentResult) -> list[str]:
    if result.validation is None:
        return []
    if result.validation.is_valid:
        return ["约束校验", "  已通过全部硬约束校验"]
    return [
        "约束校验",
        *(f"  - {violation.message}" for violation in result.validation.errors),
    ]


def _format_traces(result: AgentResult) -> list[str]:
    lines = ["Agent执行轨迹"]
    for trace in result.traces:
        status = _TRACE_STATUS_LABELS.get(trace.status, trace.status)
        lines.append(f"  [{status}] {trace.step}：{trace.message}")
    return lines


def format_agent_result(result: AgentResult, *, show_trace: bool = False) -> str:
    lines = ["杭州旅行规划 Agent", "=" * 24]
    if result.request is not None:
        lines.extend(_format_request(result.request))
    if result.errors:
        lines.extend(["", "无法生成完整行程"])
        lines.extend(f"  - {message}" for message in result.errors)
    if result.plan is not None:
        lines.extend(["", *_format_itinerary(result)])
        lines.extend(["", *_format_budget(result)])
        notices = _format_data_notices(result)
        if notices:
            lines.extend(["", *notices])
        validation = _format_validation(result)
        if validation:
            lines.extend(["", *validation])
        narrative = format_natural_language_output(result.to_dict())
        if narrative:
            lines.extend(["", "自然语言行程说明"])
            lines.extend(f"  {paragraph}" for paragraph in narrative.splitlines())
    if show_trace and result.traces:
        lines.extend(["", *_format_traces(result)])
    return "\n".join(lines)


def format_runtime_error(message: str) -> str:
    return "\n".join(
        ["杭州旅行规划 Agent", "=" * 24, "", "运行失败", f"  - {message}"]
    )
