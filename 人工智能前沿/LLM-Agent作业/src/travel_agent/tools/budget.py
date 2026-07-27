from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from travel_agent.config import AppConfig
from travel_agent.models import BudgetSummary, DailyItinerary, POI, TravelRequest


@dataclass(frozen=True, slots=True)
class CostEstimate:
    amount_yuan: float
    estimated: bool = False
    warning: str | None = None


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    unknown_ticket_estimate_yuan: float = 0.0
    meal_per_person_per_day_yuan: float = 100.0
    taxi_base_fare_yuan: float = 13.0
    taxi_base_distance_km: float = 3.0
    taxi_per_km_yuan: float = 2.5
    taxi_capacity: int = 4

    @classmethod
    def from_config(cls, config: AppConfig) -> BudgetPolicy:
        return cls(
            unknown_ticket_estimate_yuan=config.unknown_ticket_estimate_yuan,
            meal_per_person_per_day_yuan=config.meal_budget_per_person_per_day,
            taxi_base_fare_yuan=config.taxi_base_fare_yuan,
            taxi_base_distance_km=config.taxi_base_distance_km,
            taxi_per_km_yuan=config.taxi_per_km_yuan,
        )


class BudgetTool:
    def __init__(self, policy: BudgetPolicy | None = None) -> None:
        self.policy = policy or BudgetPolicy()

    def estimate_ticket(self, poi: POI, travelers: int) -> CostEstimate:
        if travelers <= 0:
            raise ValueError("travelers must be positive")
        if poi.ticket_price_yuan is None:
            return CostEstimate(
                amount_yuan=self.policy.unknown_ticket_estimate_yuan * travelers,
                estimated=True,
                warning=f"{poi.name}门票未知，暂按每人"
                f"{self.policy.unknown_ticket_estimate_yuan:.0f}元估算",
            )
        return CostEstimate(amount_yuan=poi.ticket_price_yuan * travelers)

    def estimate_transport(
        self,
        distance_m: int,
        mode: str,
        travelers: int,
    ) -> CostEstimate:
        if distance_m < 0 or travelers <= 0:
            raise ValueError("distance cannot be negative and travelers must be positive")
        normalized_mode = mode.strip().lower()
        if normalized_mode in {"walk", "walking"}:
            return CostEstimate(amount_yuan=0.0)
        if normalized_mode == "taxi":
            distance_km = distance_m / 1000
            extra_km = max(0.0, distance_km - self.policy.taxi_base_distance_km)
            fare_per_vehicle = (
                self.policy.taxi_base_fare_yuan
                + extra_km * self.policy.taxi_per_km_yuan
            )
            vehicle_count = math.ceil(travelers / self.policy.taxi_capacity)
            return CostEstimate(
                amount_yuan=fare_per_vehicle * vehicle_count,
                estimated=True,
                warning="出租车费用按距离和基础计价规则估算，不代表实际结算金额",
            )
        if normalized_mode == "driving":
            return CostEstimate(
                amount_yuan=0.0,
                estimated=True,
                warning="自驾油费、停车费和高速费尚未计入",
            )
        raise ValueError(f"unsupported transport mode: {mode}")

    def summarize(
        self,
        request: TravelRequest,
        days: Iterable[DailyItinerary],
    ) -> BudgetSummary:
        day_list = tuple(days)
        ticket_yuan = sum(
            item.ticket_cost_yuan for day in day_list for item in day.items
        )
        transport_yuan = sum(
            item.transport_cost_yuan for day in day_list for item in day.items
        )
        meal_yuan = (
            self.policy.meal_per_person_per_day_yuan
            * request.travelers.total
            * len(day_list)
        )
        unknown_ticket_pois = tuple(
            dict.fromkeys(
                item.poi.name
                for day in day_list
                for item in day.items
                if "ticket_cost_yuan" in item.estimated_fields
            )
        )
        total_yuan = ticket_yuan + transport_yuan + meal_yuan
        remaining = (
            None
            if request.budget_yuan is None
            else request.budget_yuan - total_yuan
        )
        warnings: list[str] = []
        if unknown_ticket_pois:
            warnings.append("部分景点门票未知，预算包含开发阶段估算值")
        if any(
            "transport_cost_yuan" in item.estimated_fields
            for day in day_list
            for item in day.items
        ):
            warnings.append("交通费用为估算值")
        return BudgetSummary(
            ticket_yuan=ticket_yuan,
            transport_yuan=transport_yuan,
            meal_yuan=meal_yuan,
            total_yuan=total_yuan,
            budget_yuan=request.budget_yuan,
            remaining_yuan=remaining,
            unknown_ticket_pois=unknown_ticket_pois,
            estimated=bool(unknown_ticket_pois or warnings),
            warnings=tuple(warnings),
        )

