from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from travel_agent.data import POIRepository
from travel_agent.models import (
    POI,
    POIQuery,
    TravelRequest,
    WalkLevel,
    compact_text,
    normalize_text,
)


PREFERENCE_CATEGORY_MAP: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "历史": ("museum", "historic_site", "temple", "ancient_town"),
        "人文": (
            "museum",
            "historic_site",
            "temple",
            "ancient_town",
            "cultural_district",
        ),
        "文化": (
            "museum",
            "historic_site",
            "temple",
            "ancient_town",
            "cultural_district",
        ),
        "博物馆": ("museum",),
        "艺术": ("art_gallery", "exhibition", "museum"),
        "美术馆": ("art_gallery",),
        "展览": ("exhibition", "art_gallery"),
        "自然": ("scenic_area", "park", "wetland"),
        "户外": (
            "scenic_area",
            "park",
            "wetland",
            "ancient_town",
            "pedestrian_street",
        ),
        "公园": ("park", "wetland"),
        "湿地": ("wetland",),
        "亲子": ("zoo", "park", "museum"),
        "动物": ("zoo",),
        "古镇": ("ancient_town", "historic_site", "cultural_district"),
        "城市": ("cultural_district", "pedestrian_street", "exhibition"),
        "街区": ("cultural_district", "pedestrian_street"),
        "购物": ("pedestrian_street", "cultural_district"),
    }
)

_KNOWN_CATEGORIES = frozenset(
    category
    for categories in PREFERENCE_CATEGORY_MAP.values()
    for category in categories
)
_WALK_LEVEL_RANK = {
    WalkLevel.LOW: 1,
    WalkLevel.MEDIUM: 2,
    WalkLevel.HIGH: 3,
}


def _clean_tuple(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for raw_value in values:
        value = str(raw_value).strip()
        normalized = normalize_text(value)
        if value and normalized not in seen:
            result.append(value)
            seen.add(normalized)
    return tuple(result)


@dataclass(frozen=True, slots=True)
class POISearchInput:
    """Structured travel preferences accepted by the POI search tool."""

    preferences: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    districts: tuple[str, ...] = ()
    must_visit: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    indoor_preferred: bool = False
    requires_reservation: bool | None = None
    max_walk_level: WalkLevel | None = None
    planning_ready_only: bool = False
    include_unknown: bool = True
    diversify: bool = True
    max_per_category: int = 4
    limit: int = 20

    def __post_init__(self) -> None:
        for field_name in (
            "preferences",
            "categories",
            "districts",
            "must_visit",
            "avoid",
        ):
            object.__setattr__(self, field_name, _clean_tuple(getattr(self, field_name)))

        if isinstance(self.max_walk_level, str):
            try:
                object.__setattr__(self, "max_walk_level", WalkLevel(self.max_walk_level))
            except ValueError as exc:
                raise ValueError("max_walk_level must be low, medium or high") from exc
        if not (1 <= self.limit <= 100):
            raise ValueError("limit must be between 1 and 100")
        if self.max_per_category < 1:
            raise ValueError("max_per_category must be positive")
        if len(self.must_visit) > self.limit:
            raise ValueError("limit cannot be smaller than the number of must-visit POIs")

    @classmethod
    def from_travel_request(
        cls,
        request: TravelRequest,
        *,
        districts: tuple[str, ...] | None = None,
        limit: int = 20,
    ) -> POISearchInput:
        return cls(
            preferences=request.preferences,
            districts=request.districts if districts is None else districts,
            must_visit=request.must_visit,
            avoid=request.avoid,
            indoor_preferred=request.indoor_preferred,
            max_walk_level=request.max_walk_level,
            limit=limit,
        )


@dataclass(frozen=True, slots=True)
class CandidatePOI:
    poi: POI
    score: float
    matched_preferences: tuple[str, ...]
    selection_reasons: tuple[str, ...]
    data_warnings: tuple[str, ...]
    is_must_visit: bool = False


@dataclass(frozen=True, slots=True)
class POISearchResponse:
    candidates: tuple[CandidatePOI, ...]
    applied_categories: tuple[str, ...]
    unmapped_preferences: tuple[str, ...]
    unresolved_must_visit: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def pois(self) -> tuple[POI, ...]:
        return tuple(candidate.poi for candidate in self.candidates)


@dataclass(frozen=True, slots=True)
class _MustVisitMatch:
    requested_name: str
    poi: POI
    exact: bool


class POISearchTool:
    """Select and rank candidate POIs from structured travel preferences."""

    def __init__(self, repository: POIRepository) -> None:
        self._repository = repository

    def search(self, criteria: POISearchInput) -> POISearchResponse:
        applied_categories, mapped_preferences, unmapped_preferences = (
            self._resolve_categories(criteria)
        )
        must_matches, unresolved_must_visit = self._resolve_must_visit(
            criteria.must_visit
        )
        must_by_id = {match.poi.id: match for match in must_matches}

        pool = self._repository.filter(
            POIQuery(
                categories=applied_categories,
                districts=criteria.districts,
                requires_reservation=criteria.requires_reservation,
                max_walk_level=criteria.max_walk_level,
                planning_ready_only=criteria.planning_ready_only,
                include_unknown=criteria.include_unknown,
                limit=len(self._repository),
            )
        )

        warnings: list[str] = []
        if unmapped_preferences:
            warnings.append(
                "以下偏好没有预设类别映射，将仅使用文本匹配："
                + "、".join(unmapped_preferences)
            )
        if unresolved_must_visit:
            warnings.append(
                "以下必去景点未在POI数据中找到："
                + "、".join(unresolved_must_visit)
            )

        candidate_by_id: dict[str, POI] = {poi.id: poi for poi in pool}
        for match in must_matches:
            candidate_by_id[match.poi.id] = match.poi
            if not match.exact:
                warnings.append(
                    f"必去景点“{match.requested_name}”使用模糊名称匹配为“{match.poi.name}”"
                )

        avoid_terms = tuple(compact_text(term) for term in criteria.avoid)
        scored: list[CandidatePOI] = []
        for poi in candidate_by_id.values():
            must_match = must_by_id.get(poi.id)
            if self._is_avoided(poi, avoid_terms):
                if must_match is None:
                    continue
                warnings.append(
                    f"必去景点“{poi.name}”同时命中避开条件，按必去要求保留"
                )
            candidate = self._score_candidate(
                poi=poi,
                criteria=criteria,
                mapped_preferences=mapped_preferences,
                must_match=must_match,
            )
            if (
                criteria.preferences
                and not candidate.matched_preferences
                and not candidate.is_must_visit
            ):
                continue
            scored.append(candidate)

        scored.sort(
            key=lambda candidate: (
                not candidate.is_must_visit,
                -candidate.score,
                normalize_text(candidate.poi.name),
                candidate.poi.id,
            )
        )
        selected = self._select_diverse(scored, criteria)

        if not selected:
            warnings.append("当前筛选条件没有返回任何候选POI")
        elif len(selected) < criteria.limit:
            warnings.append(
                f"当前条件仅找到{len(selected)}个候选POI，少于请求的{criteria.limit}个"
            )

        return POISearchResponse(
            candidates=selected,
            applied_categories=applied_categories,
            unmapped_preferences=unmapped_preferences,
            unresolved_must_visit=unresolved_must_visit,
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def _resolve_categories(
        self, criteria: POISearchInput
    ) -> tuple[tuple[str, ...], Mapping[str, tuple[str, ...]], tuple[str, ...]]:
        categories: list[str] = list(criteria.categories)
        mapped_preferences: dict[str, tuple[str, ...]] = {}
        unmapped_preferences: list[str] = []

        for preference in criteria.preferences:
            normalized_preference = compact_text(preference)
            matched: list[str] = []
            if normalize_text(preference) in _KNOWN_CATEGORIES:
                matched.append(normalize_text(preference))

            for label, label_categories in PREFERENCE_CATEGORY_MAP.items():
                normalized_label = compact_text(label)
                if (
                    normalized_label == normalized_preference
                    or normalized_label in normalized_preference
                    or normalized_preference in normalized_label
                ):
                    for category in label_categories:
                        if category not in matched:
                            matched.append(category)

            if matched:
                mapped_preferences[preference] = tuple(matched)
                categories.extend(matched)
            else:
                unmapped_preferences.append(preference)

        return (
            _clean_tuple(categories),
            MappingProxyType(mapped_preferences),
            tuple(unmapped_preferences),
        )

    def _resolve_must_visit(
        self, requested_names: tuple[str, ...]
    ) -> tuple[tuple[_MustVisitMatch, ...], tuple[str, ...]]:
        matches: list[_MustVisitMatch] = []
        unresolved: list[str] = []
        used_ids: set[str] = set()

        for requested_name in requested_names:
            exact_matches = self._repository.find_by_name(requested_name, exact=True)
            if exact_matches:
                poi = exact_matches[0]
                exact = True
            else:
                fuzzy_matches = self._repository.search(
                    POIQuery(text=requested_name, limit=5)
                )
                if not fuzzy_matches:
                    unresolved.append(requested_name)
                    continue
                poi = fuzzy_matches[0]
                exact = False

            if poi.id not in used_ids:
                matches.append(
                    _MustVisitMatch(
                        requested_name=requested_name,
                        poi=poi,
                        exact=exact,
                    )
                )
                used_ids.add(poi.id)

        return tuple(matches), tuple(unresolved)

    def _score_candidate(
        self,
        poi: POI,
        criteria: POISearchInput,
        mapped_preferences: Mapping[str, tuple[str, ...]],
        must_match: _MustVisitMatch | None,
    ) -> CandidatePOI:
        score = 0.0
        reasons: list[str] = []
        matched_preferences: list[str] = []

        if must_match is not None:
            score += 1000.0
            match_type = "精确匹配" if must_match.exact else "模糊匹配"
            reasons.append(f"必去景点（{match_type}）")

        searchable_fields = (
            compact_text(poi.name),
            compact_text(poi.category),
            *(compact_text(tag) for tag in poi.tags),
        )
        for preference in criteria.preferences:
            preference_categories = mapped_preferences.get(preference, ())
            text_preference = compact_text(preference)
            category_match = poi.category in preference_categories
            text_match = bool(text_preference) and any(
                text_preference in value or value in text_preference
                for value in searchable_fields
                if value
            )
            if category_match or text_match:
                score += 30.0
                matched_preferences.append(preference)
                reasons.append(f"符合“{preference}”偏好")

        normalized_categories = {
            normalize_text(category) for category in criteria.categories
        }
        if (
            normalized_categories
            and normalize_text(poi.category) in normalized_categories
        ):
            score += 10.0
            reasons.append("符合指定POI类别")
        normalized_districts = {
            normalize_text(district) for district in criteria.districts
        }
        if (
            normalized_districts
            and normalize_text(poi.district) in normalized_districts
        ):
            score += 15.0
            reasons.append(f"位于{poi.district}")

        if criteria.indoor_preferred:
            if poi.indoor is True:
                score += 15.0
                reasons.append("适合室内游览")
            elif poi.indoor is None:
                reasons.append("室内外属性未知")

        if criteria.max_walk_level is not None and poi.walk_level is not None:
            if (
                _WALK_LEVEL_RANK[poi.walk_level]
                <= _WALK_LEVEL_RANK[criteria.max_walk_level]
            ):
                score += 10.0
                reasons.append("步行强度符合要求")

        if poi.planning_ready:
            score += 10.0
            reasons.append("规划所需数据已核验")
        else:
            if poi.opening_hours.is_complete:
                score += 4.0
            if poi.ticket_price_yuan is not None:
                score += 3.0
            if poi.requires_reservation is not None:
                score += 2.0
            if poi.walk_level is not None:
                score += 1.0

        return CandidatePOI(
            poi=poi,
            score=score,
            matched_preferences=tuple(matched_preferences),
            selection_reasons=tuple(dict.fromkeys(reasons)),
            data_warnings=self._data_warnings(poi),
            is_must_visit=must_match is not None,
        )

    @staticmethod
    def _data_warnings(poi: POI) -> tuple[str, ...]:
        warnings: list[str] = []
        if not poi.opening_hours.is_complete:
            warnings.append("开放时间未核验")
        if poi.ticket_price_yuan is None:
            warnings.append("门票价格未知")
        if poi.requires_reservation is None:
            warnings.append("预约要求未知")
        if poi.walk_level is None:
            warnings.append("步行强度未知")
        return tuple(warnings)

    @staticmethod
    def _is_avoided(poi: POI, avoid_terms: tuple[str, ...]) -> bool:
        if not avoid_terms:
            return False
        searchable_fields = (
            compact_text(poi.name),
            compact_text(poi.category),
            compact_text(poi.district),
            compact_text(poi.address),
            *(compact_text(tag) for tag in poi.tags),
        )
        return any(
            avoid_term in field
            for avoid_term in avoid_terms
            for field in searchable_fields
            if avoid_term and field
        )

    @staticmethod
    def _select_diverse(
        candidates: list[CandidatePOI], criteria: POISearchInput
    ) -> tuple[CandidatePOI, ...]:
        if not criteria.diversify:
            return tuple(candidates[: criteria.limit])

        selected: list[CandidatePOI] = []
        selected_ids: set[str] = set()
        selected_names: set[str] = set()
        category_counts: dict[str, int] = {}

        for candidate in candidates:
            if not candidate.is_must_visit:
                continue
            normalized_name = compact_text(candidate.poi.name)
            if candidate.poi.id in selected_ids or normalized_name in selected_names:
                continue
            selected.append(candidate)
            selected_ids.add(candidate.poi.id)
            selected_names.add(normalized_name)
            category_counts[candidate.poi.category] = (
                category_counts.get(candidate.poi.category, 0) + 1
            )

        deferred: list[CandidatePOI] = []
        for candidate in candidates:
            normalized_name = compact_text(candidate.poi.name)
            if candidate.poi.id in selected_ids or normalized_name in selected_names:
                continue
            category_count = category_counts.get(candidate.poi.category, 0)
            if category_count >= criteria.max_per_category:
                deferred.append(candidate)
                continue
            selected.append(candidate)
            selected_ids.add(candidate.poi.id)
            selected_names.add(normalized_name)
            category_counts[candidate.poi.category] = category_count + 1
            if len(selected) >= criteria.limit:
                return tuple(selected[: criteria.limit])

        for candidate in deferred:
            normalized_name = compact_text(candidate.poi.name)
            if candidate.poi.id in selected_ids or normalized_name in selected_names:
                continue
            selected.append(candidate)
            selected_ids.add(candidate.poi.id)
            selected_names.add(normalized_name)
            if len(selected) >= criteria.limit:
                break
        return tuple(selected[: criteria.limit])
