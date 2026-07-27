from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travel_agent.models import (
    POI,
    POIQuery,
    POISearchResult,
    WalkLevel,
    compact_text,
    normalize_text,
)


DEFAULT_POI_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "hangzhou_pois.jsonl"
)
_QUERY_TOKEN_PATTERN = re.compile(r"[\s,，。.;；:：/\\|]+")
_WALK_LEVEL_RANK = {
    WalkLevel.LOW: 1,
    WalkLevel.MEDIUM: 2,
    WalkLevel.HIGH: 3,
}


class POIDataError(RuntimeError):
    """Raised when a POI dataset cannot be loaded safely."""


@dataclass(frozen=True, slots=True)
class POILoadIssue:
    line_number: int
    message: str
    raw_excerpt: str


@dataclass(frozen=True, slots=True)
class POILoadReport:
    source_path: Path
    total_lines: int
    loaded_count: int
    skipped_count: int
    issues: tuple[POILoadIssue, ...] = ()


class POIRepository:
    """Immutable, indexed access to a validated JSONL POI snapshot."""

    def __init__(self, pois: Sequence[POI], report: POILoadReport) -> None:
        self._pois = tuple(pois)
        self._report = report
        self._by_id: dict[str, POI] = {poi.id: poi for poi in self._pois}
        self._category_index = self._build_index("category")
        self._district_index = self._build_index("district")
        self._tag_index = self._build_tag_index()

    @classmethod
    def from_jsonl(
        cls,
        path: str | Path = DEFAULT_POI_PATH,
        *,
        strict: bool = True,
    ) -> POIRepository:
        source_path = Path(path).expanduser().resolve()
        if not source_path.is_file():
            raise POIDataError(f"POI dataset does not exist: {source_path}")

        pois: list[POI] = []
        issues: list[POILoadIssue] = []
        seen_ids: set[str] = set()
        total_lines = 0

        try:
            with source_path.open("r", encoding="utf-8") as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    if not raw_line.strip():
                        continue
                    total_lines += 1
                    try:
                        raw = json.loads(raw_line)
                        if not isinstance(raw, dict):
                            raise ValueError("each JSONL line must contain an object")
                        poi = POI.from_mapping(raw)
                        if poi.id in seen_ids:
                            raise ValueError(f"duplicate POI id: {poi.id}")
                    except (json.JSONDecodeError, TypeError, ValueError) as exc:
                        issue = POILoadIssue(
                            line_number=line_number,
                            message=str(exc),
                            raw_excerpt=raw_line.strip()[:200],
                        )
                        if strict:
                            raise POIDataError(
                                f"Invalid POI at {source_path}:{line_number}: {exc}"
                            ) from exc
                        issues.append(issue)
                        continue

                    pois.append(poi)
                    seen_ids.add(poi.id)
        except OSError as exc:
            raise POIDataError(f"Cannot read POI dataset: {source_path}") from exc

        if not pois:
            raise POIDataError(f"POI dataset contains no usable records: {source_path}")

        report = POILoadReport(
            source_path=source_path,
            total_lines=total_lines,
            loaded_count=len(pois),
            skipped_count=len(issues),
            issues=tuple(issues),
        )
        return cls(pois, report)

    @property
    def report(self) -> POILoadReport:
        return self._report

    def __len__(self) -> int:
        return len(self._pois)

    def __iter__(self) -> Iterator[POI]:
        return iter(self._pois)

    def _build_index(self, attribute: str) -> dict[str, tuple[POI, ...]]:
        index: dict[str, list[POI]] = defaultdict(list)
        for poi in self._pois:
            index[normalize_text(str(getattr(poi, attribute)))].append(poi)
        return {key: tuple(values) for key, values in index.items()}

    def _build_tag_index(self) -> dict[str, tuple[POI, ...]]:
        index: dict[str, list[POI]] = defaultdict(list)
        for poi in self._pois:
            for tag in poi.tags:
                index[normalize_text(tag)].append(poi)
        return {key: tuple(values) for key, values in index.items()}

    def all(self, *, planning_ready_only: bool = False) -> tuple[POI, ...]:
        if not planning_ready_only:
            return self._pois
        return tuple(poi for poi in self._pois if poi.planning_ready)

    def get(self, poi_id: str) -> POI | None:
        return self._by_id.get(poi_id)

    def get_required(self, poi_id: str) -> POI:
        poi = self.get(poi_id)
        if poi is None:
            raise KeyError(f"unknown POI id: {poi_id}")
        return poi

    def by_category(self, category: str) -> tuple[POI, ...]:
        return self._category_index.get(normalize_text(category), ())

    def by_district(self, district: str) -> tuple[POI, ...]:
        return self._district_index.get(normalize_text(district), ())

    def by_tag(self, tag: str) -> tuple[POI, ...]:
        return self._tag_index.get(normalize_text(tag), ())

    def find_by_name(
        self, name: str, *, exact: bool = False, limit: int = 20
    ) -> tuple[POI, ...]:
        query = compact_text(name)
        if not query or limit < 1:
            return ()

        matches: list[tuple[int, POI]] = []
        for poi in self._pois:
            normalized_name = compact_text(poi.name)
            if normalized_name == query:
                matches.append((0, poi))
            elif not exact and query in normalized_name:
                matches.append((1, poi))
        matches.sort(key=lambda item: (item[0], normalize_text(item[1].name), item[1].id))
        return tuple(poi for _, poi in matches[:limit])

    def filter(self, query: POIQuery | None = None) -> tuple[POI, ...]:
        query = query or POIQuery(limit=len(self._pois))
        category_filters = {normalize_text(value) for value in query.categories}
        district_filters = {normalize_text(value) for value in query.districts}
        tags_any = {normalize_text(value) for value in query.tags_any}
        tags_all = {normalize_text(value) for value in query.tags_all}

        selected: list[POI] = []
        for poi in self._pois:
            if query.planning_ready_only and not poi.planning_ready:
                continue
            if category_filters and normalize_text(poi.category) not in category_filters:
                continue
            if district_filters and normalize_text(poi.district) not in district_filters:
                continue

            poi_tags = {normalize_text(tag) for tag in poi.tags}
            if tags_any and poi_tags.isdisjoint(tags_any):
                continue
            if tags_all and not tags_all.issubset(poi_tags):
                continue
            if not self._matches_optional_bool(
                poi.indoor, query.indoor, query.include_unknown
            ):
                continue
            if not self._matches_optional_bool(
                poi.requires_reservation,
                query.requires_reservation,
                query.include_unknown,
            ):
                continue
            if not self._matches_walk_level(
                poi.walk_level, query.max_walk_level, query.include_unknown
            ):
                continue
            selected.append(poi)

        return tuple(selected[: query.limit])

    @staticmethod
    def _matches_optional_bool(
        actual: bool | None,
        expected: bool | None,
        include_unknown: bool,
    ) -> bool:
        if expected is None:
            return True
        if actual is None:
            return include_unknown
        return actual is expected

    @staticmethod
    def _matches_walk_level(
        actual: WalkLevel | None,
        maximum: WalkLevel | None,
        include_unknown: bool,
    ) -> bool:
        if maximum is None:
            return True
        if actual is None:
            return include_unknown
        return _WALK_LEVEL_RANK[actual] <= _WALK_LEVEL_RANK[maximum]

    def search_with_scores(self, query: POIQuery) -> tuple[POISearchResult, ...]:
        candidates = self.filter(
            POIQuery(
                categories=query.categories,
                districts=query.districts,
                tags_any=query.tags_any,
                tags_all=query.tags_all,
                indoor=query.indoor,
                requires_reservation=query.requires_reservation,
                max_walk_level=query.max_walk_level,
                planning_ready_only=query.planning_ready_only,
                include_unknown=query.include_unknown,
                limit=len(self._pois),
            )
        )

        results: list[POISearchResult] = []
        for poi in candidates:
            score, matched_fields = self._text_score(poi, query.text)
            if query.text and score <= 0:
                continue
            results.append(
                POISearchResult(
                    poi=poi,
                    score=score,
                    matched_fields=matched_fields,
                )
            )

        results.sort(
            key=lambda result: (
                -result.score,
                normalize_text(result.poi.name),
                result.poi.id,
            )
        )
        return tuple(results[: query.limit])

    def search(self, query: POIQuery) -> tuple[POI, ...]:
        return tuple(result.poi for result in self.search_with_scores(query))

    @staticmethod
    def _text_score(poi: POI, query_text: str | None) -> tuple[float, tuple[str, ...]]:
        if not query_text:
            return 0.0, ()

        raw_tokens = [
            token
            for token in _QUERY_TOKEN_PATTERN.split(query_text.strip())
            if token.strip()
        ]
        tokens = [compact_text(token) for token in raw_tokens]
        tokens = [token for token in tokens if token]
        if not tokens:
            return 0.0, ()

        fields: dict[str, tuple[str, ...]] = {
            "name": (compact_text(poi.name),),
            "tags": tuple(compact_text(tag) for tag in poi.tags),
            "category": (compact_text(poi.category),),
            "district": (compact_text(poi.district),),
            "address": (compact_text(poi.address),),
        }
        weights = {
            "name": (100.0, 70.0),
            "tags": (55.0, 35.0),
            "category": (40.0, 25.0),
            "district": (35.0, 20.0),
            "address": (20.0, 10.0),
        }

        total_score = 0.0
        matched_fields: set[str] = set()
        for token in tokens:
            best_score = 0.0
            best_field: str | None = None
            for field_name, values in fields.items():
                exact_weight, contains_weight = weights[field_name]
                for value in values:
                    if not value:
                        continue
                    if value == token:
                        candidate_score = exact_weight
                    elif token in value or value in token:
                        candidate_score = contains_weight
                    else:
                        continue
                    if candidate_score > best_score:
                        best_score = candidate_score
                        best_field = field_name
            total_score += best_score
            if best_field:
                matched_fields.add(best_field)

        return total_score, tuple(sorted(matched_fields))

    def statistics(self) -> dict[str, Any]:
        return {
            "total": len(self._pois),
            "planning_ready": sum(poi.planning_ready for poi in self._pois),
            "categories": dict(Counter(poi.category for poi in self._pois)),
            "districts": dict(Counter(poi.district for poi in self._pois)),
            "unknown_opening_hours": sum(
                not poi.opening_hours.is_complete for poi in self._pois
            ),
            "unknown_ticket_price": sum(
                poi.ticket_price_yuan is None for poi in self._pois
            ),
        }

