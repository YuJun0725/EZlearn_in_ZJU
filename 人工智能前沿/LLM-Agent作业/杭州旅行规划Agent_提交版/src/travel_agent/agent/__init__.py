"""Deterministic orchestration for the travel-planning agent."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .graph import AgentResult, TravelPlanningAgent

__all__ = ["AgentResult", "TravelPlanningAgent"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from .graph import AgentResult, TravelPlanningAgent

        return {"AgentResult": AgentResult, "TravelPlanningAgent": TravelPlanningAgent}[
            name
        ]
    raise AttributeError(name)
