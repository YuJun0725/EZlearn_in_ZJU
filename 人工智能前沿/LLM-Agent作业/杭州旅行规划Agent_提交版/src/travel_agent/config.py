from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return default if raw is None else float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return default if raw is None else int(raw)


@dataclass(frozen=True, slots=True)
class AppConfig:
    poi_data_path: Path = PROJECT_ROOT / "data" / "processed" / "hangzhou_pois.jsonl"
    default_opening_time: str = "09:00"
    default_closing_time: str = "17:00"
    default_visit_duration_min: int = 90
    unknown_ticket_estimate_yuan: float = 0.0
    meal_budget_per_person_per_day: float = 100.0
    taxi_base_fare_yuan: float = 13.0
    taxi_base_distance_km: float = 3.0
    taxi_per_km_yuan: float = 2.5
    max_pois_per_day: int = 4
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None

    def __post_init__(self) -> None:
        if self.default_visit_duration_min <= 0:
            raise ValueError("default_visit_duration_min must be positive")
        if self.max_pois_per_day <= 0:
            raise ValueError("max_pois_per_day must be positive")
        numeric_values = (
            self.unknown_ticket_estimate_yuan,
            self.meal_budget_per_person_per_day,
            self.taxi_base_fare_yuan,
            self.taxi_base_distance_km,
            self.taxi_per_km_yuan,
        )
        if min(numeric_values) < 0:
            raise ValueError("budget and taxi configuration cannot be negative")

    @classmethod
    def from_env(cls, env_path: str | Path = PROJECT_ROOT / ".env") -> AppConfig:
        _load_env_file(Path(env_path))
        return cls(
            poi_data_path=Path(
                os.environ.get(
                    "POI_DATA_PATH",
                    str(PROJECT_ROOT / "data" / "processed" / "hangzhou_pois.jsonl"),
                )
            ),
            default_opening_time=os.environ.get("DEFAULT_OPENING_TIME", "09:00"),
            default_closing_time=os.environ.get("DEFAULT_CLOSING_TIME", "17:00"),
            default_visit_duration_min=_env_int("DEFAULT_VISIT_DURATION_MIN", 90),
            unknown_ticket_estimate_yuan=_env_float(
                "UNKNOWN_TICKET_ESTIMATE_YUAN", 0.0
            ),
            meal_budget_per_person_per_day=_env_float(
                "MEAL_BUDGET_PER_PERSON_PER_DAY", 100.0
            ),
            taxi_base_fare_yuan=_env_float("TAXI_BASE_FARE_YUAN", 13.0),
            taxi_base_distance_km=_env_float("TAXI_BASE_DISTANCE_KM", 3.0),
            taxi_per_km_yuan=_env_float("TAXI_PER_KM_YUAN", 2.5),
            max_pois_per_day=_env_int("MAX_POIS_PER_DAY", 4),
            llm_api_key=os.environ.get("LLM_API_KEY") or None,
            llm_base_url=os.environ.get("LLM_BASE_URL") or None,
            llm_model=os.environ.get("LLM_MODEL") or None,
        )

