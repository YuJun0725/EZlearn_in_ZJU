from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Any

from travel_agent.config import AppConfig
from travel_agent.data import POIRepository
from travel_agent.llm import LLMClientError, OpenAICompatibleClient
from travel_agent.models import (
    ToolTrace,
    TravelRequest,
    TripPlan,
    ValidationReport,
    normalize_text,
)
from travel_agent.planner import ItineraryOptimizer, ItineraryPlanner, ItineraryValidator
from travel_agent.tools import (
    AmapRouteTool,
    AmapWeatherError,
    AmapWeatherTool,
    CandidatePOI,
    DailyWeather,
    POISearchInput,
    POISearchResponse,
    POISearchTool,
)


@dataclass(frozen=True, slots=True)
class AgentResult:
    status: str
    request: TravelRequest | None
    plan: TripPlan | None
    validation: ValidationReport | None
    traces: tuple[ToolTrace, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def is_success(self) -> bool:
        return self.status == "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request": self.request.to_dict() if self.request else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "traces": [trace.to_dict() for trace in self.traces],
            "errors": list(self.errors),
        }


class TravelPlanningAgent:
    """Explicit state machine coordinating tools and deterministic planning."""

    def __init__(
        self,
        config: AppConfig,
        repository: POIRepository,
        *,
        weather_tool: AmapWeatherTool | None = None,
        route_tool: AmapRouteTool | None = None,
        llm_client: OpenAICompatibleClient | None = None,
    ) -> None:
        self.config = config
        self.repository = repository
        self.search_tool = POISearchTool(repository)
        self.weather_tool = weather_tool
        self.route_tool = route_tool
        self.llm_client = llm_client
        self.planner = ItineraryPlanner(config, route_tool=route_tool)
        self.validator = ItineraryValidator()

    @classmethod
    def from_config(
        cls,
        config: AppConfig | None = None,
        *,
        enable_weather: bool = False,
        enable_routes: bool = False,
        enable_llm: bool = False,
    ) -> TravelPlanningAgent:
        config = config or AppConfig.from_env()
        repository = POIRepository.from_jsonl(config.poi_data_path)
        return cls(
            config,
            repository,
            weather_tool=AmapWeatherTool.from_env() if enable_weather else None,
            route_tool=AmapRouteTool.from_env() if enable_routes else None,
            llm_client=(
                OpenAICompatibleClient.from_config(config) if enable_llm else None
            ),
        )

    def run_text(
        self,
        user_text: str,
        *,
        use_live_weather: bool = False,
        use_live_routes: bool = False,
    ) -> AgentResult:
        if self.llm_client is None:
            message = "自然语言输入需要配置并启用 LLM 客户端"
            return AgentResult(
                status="failed",
                request=None,
                plan=None,
                validation=None,
                traces=(ToolTrace("parse_request", "failed", message),),
                errors=(message,),
            )
        try:
            request = self.llm_client.parse_travel_request(user_text)
        except LLMClientError as exc:
            message = str(exc)
            return AgentResult(
                status="failed",
                request=None,
                plan=None,
                validation=None,
                traces=(ToolTrace("parse_request", "failed", message),),
                errors=(message,),
            )
        parse_trace = ToolTrace(
            "parse_request",
            "completed",
            "自然语言需求已转换为 TravelRequest",
            {"model": self.llm_client.model},
        )
        result = self.run(
            request,
            use_live_weather=use_live_weather,
            use_live_routes=use_live_routes,
        )
        return replace(result, traces=(parse_trace, *result.traces))

    def run(
        self,
        request: TravelRequest,
        *,
        use_live_weather: bool = False,
        use_live_routes: bool = False,
    ) -> AgentResult:
        traces: list[ToolTrace] = []
        request_errors = self._request_errors(request)
        if request_errors:
            traces.append(
                ToolTrace(
                    "validate_request",
                    "failed",
                    "旅行需求缺少运行所需信息",
                    {"errors": list(request_errors)},
                )
            )
            return AgentResult(
                "failed", request, None, None, tuple(traces), request_errors
            )
        traces.append(
            ToolTrace(
                "validate_request",
                "completed",
                "旅行需求校验通过",
                {"days": request.days, "travelers": request.travelers.total},
            )
        )

        weather_by_date = self._load_weather(
            request, use_live_weather=use_live_weather, traces=traces
        )
        weather_indoor = any(item.indoor_recommended for item in weather_by_date.values())
        search_limit = min(
            100,
            max(
                12,
                (request.days or 1) * self.config.max_pois_per_day * 2,
                len(request.must_visit),
            ),
        )
        criteria = POISearchInput.from_travel_request(request, limit=search_limit)
        if weather_indoor and not criteria.indoor_preferred:
            criteria = replace(criteria, indoor_preferred=True)
        search_response = self.search_tool.search(criteria)
        traces.append(self._search_trace(search_response, search_limit))
        if not search_response.candidates:
            message = "当前条件没有找到候选 POI"
            return AgentResult(
                "failed", request, None, None, tuple(traces), (message,)
            )

        plan = self.planner.create_plan(
            request,
            search_response.candidates,
            weather_by_date=weather_by_date,
            use_live_routes=use_live_routes and self.route_tool is not None,
        )
        traces.append(
            ToolTrace(
                "create_plan",
                "completed",
                "已生成首版行程",
                {
                    "poi_count": plan.poi_count,
                    "live_routes": use_live_routes and self.route_tool is not None,
                    "estimated_total_yuan": round(plan.budget.total_yuan, 2),
                },
            )
        )
        validation = self.validator.validate(plan)
        traces.append(self._validation_trace(validation, retry=False))

        if not validation.is_valid:
            plan, validation = self._retry_plan(
                request,
                search_response.candidates,
                weather_by_date,
                validation,
                use_live_routes=use_live_routes,
                traces=traces,
            )

        if validation.is_valid:
            traces.append(ToolTrace("complete", "completed", "行程通过硬约束校验"))
            return AgentResult(
                "completed", request, plan, validation, tuple(traces), ()
            )
        errors = tuple(item.message for item in validation.errors)
        traces.append(
            ToolTrace(
                "complete",
                "failed",
                "重规划后仍有硬约束未满足",
                {"errors": list(errors)},
            )
        )
        return AgentResult(
            "failed", request, plan, validation, tuple(traces), errors
        )

    @staticmethod
    def _request_errors(request: TravelRequest) -> tuple[str, ...]:
        errors: list[str] = []
        if request.days is None:
            errors.append("缺少旅行天数 days")
        if request.missing_information:
            errors.append("仍需补充：" + "、".join(request.missing_information))
        if normalize_text(request.city) not in {"杭州", "杭州市"}:
            errors.append("当前 POI 数据集只支持杭州市")
        return tuple(errors)

    def _load_weather(
        self,
        request: TravelRequest,
        *,
        use_live_weather: bool,
        traces: list[ToolTrace],
    ) -> dict[date, DailyWeather]:
        if not use_live_weather:
            traces.append(ToolTrace("weather", "skipped", "未启用实时天气"))
            return {}
        if self.weather_tool is None:
            traces.append(
                ToolTrace("weather", "degraded", "天气工具未启用，继续离线规划")
            )
            return {}
        if request.start_date is None:
            traces.append(
                ToolTrace("weather", "skipped", "未提供出发日期，无法匹配天气预报")
            )
            return {}
        try:
            forecast = self.weather_tool.get_forecast()
        except AmapWeatherError as exc:
            traces.append(
                ToolTrace("weather", "degraded", f"天气查询失败，继续离线规划：{exc}")
            )
            return {}
        desired_dates = {
            request.start_date + timedelta(days=offset)
            for offset in range(request.days or 0)
        }
        matched = {item.date: item for item in forecast if item.date in desired_dates}
        missing = sorted(day.isoformat() for day in desired_dates.difference(matched))
        traces.append(
            ToolTrace(
                "weather",
                "completed" if not missing else "partial",
                "已匹配旅行日期天气" if not missing else "仅部分日期有高德天气预报",
                {
                    "matched_dates": [day.isoformat() for day in sorted(matched)],
                    "missing_dates": missing,
                },
            )
        )
        return matched

    @staticmethod
    def _search_trace(response: POISearchResponse, limit: int) -> ToolTrace:
        return ToolTrace(
            "poi_search",
            "completed" if response.candidates else "failed",
            f"检索到 {len(response.candidates)} 个候选 POI",
            {
                "limit": limit,
                "categories": list(response.applied_categories),
                "unresolved_must_visit": list(response.unresolved_must_visit),
                "warnings": list(response.warnings),
            },
        )

    @staticmethod
    def _validation_trace(report: ValidationReport, *, retry: bool) -> ToolTrace:
        return ToolTrace(
            "validate_plan_retry" if retry else "validate_plan",
            "completed" if report.is_valid else "failed",
            "行程约束校验通过" if report.is_valid else "行程存在硬约束错误",
            {
                "error_count": len(report.errors),
                "warning_count": len(report.warnings),
                "error_codes": [item.code for item in report.errors],
            },
        )

    def _retry_plan(
        self,
        request: TravelRequest,
        candidates: tuple[CandidatePOI, ...],
        weather_by_date: dict[date, DailyWeather],
        first_validation: ValidationReport,
        *,
        use_live_routes: bool,
        traces: list[ToolTrace],
    ) -> tuple[TripPlan, ValidationReport]:
        error_codes = {item.code for item in first_validation.errors}
        max_per_day = self.config.max_pois_per_day
        retry_candidates = candidates
        strategy = "重新执行候选分配"
        if "BUDGET_EXCEEDED" in error_codes:
            max_per_day = max(1, max_per_day - 1)
            retry_candidates = tuple(
                replace(
                    candidate,
                    score=candidate.score
                    - (candidate.poi.ticket_price_yuan or 0.0) * 0.5,
                )
                for candidate in candidates
            )
            strategy = "降低每日 POI 数量并优先低票价候选"
        traces.append(
            ToolTrace(
                "replan",
                "started",
                strategy,
                {"trigger_errors": sorted(error_codes), "max_pois_per_day": max_per_day},
            )
        )
        retry_planner = ItineraryPlanner(
            self.config,
            optimizer=ItineraryOptimizer(
                max_pois_per_day=max_per_day,
                default_visit_duration_min=self.config.default_visit_duration_min,
            ),
            budget_tool=self.planner.budget_tool,
            route_tool=self.route_tool,
        )
        plan = retry_planner.create_plan(
            request,
            retry_candidates,
            weather_by_date=weather_by_date,
            use_live_routes=use_live_routes and self.route_tool is not None,
        )
        validation = self.validator.validate(plan)
        traces.append(self._validation_trace(validation, retry=True))
        return plan, validation
