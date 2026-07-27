from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROCESSED = PROJECT_ROOT / "data" / "processed" / "hangzhou_pois.jsonl"
DEFAULT_CORPUS = PROJECT_ROOT / "rag_baseline" / "data" / "poi_documents.jsonl"


@dataclass(frozen=True, slots=True)
class POIDocument:
    """Text chunk plus metadata exposed to the RAG prompt."""

    id: str
    name: str
    text: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "text": self.text,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> POIDocument:
        return cls(
            id=str(raw["id"]),
            name=str(raw["name"]),
            text=str(raw["text"]),
            metadata=dict(raw.get("metadata", {})),
        )


def _opening_hours(raw: dict[str, Any]) -> str:
    if raw.get("opening_hours_raw"):
        return str(raw["opening_hours_raw"])
    opening = raw.get("opening_hours") or {}
    windows: list[str] = []
    for weekday, values in opening.items():
        if values:
            windows.append(f"{weekday}:{values}")
    return "; ".join(windows) or "未知"


def poi_to_document(raw: dict[str, Any]) -> POIDocument:
    tags = "、".join(str(item) for item in raw.get("tags", [])) or "无"
    metadata = {
        "category": raw.get("category"),
        "district": raw.get("district"),
        "address": raw.get("address"),
        "longitude": raw.get("longitude"),
        "latitude": raw.get("latitude"),
        "ticket_price_yuan": raw.get("ticket_price_yuan"),
        "opening_hours": _opening_hours(raw),
        "recommended_duration_min": raw.get("recommended_duration_min"),
        "indoor": raw.get("indoor"),
        "walk_level": raw.get("walk_level"),
        "requires_reservation": raw.get("requires_reservation"),
        "tags": tags,
    }
    text = (
        f"名称：{raw.get('name', '')}\n"
        f"类别：{raw.get('category', '')}\n"
        f"区域：{raw.get('district', '')}\n"
        f"地址：{raw.get('address', '')}\n"
        f"成人票价：{raw.get('ticket_price_yuan', '未知')}元\n"
        f"开放时间：{metadata['opening_hours']}\n"
        f"建议游览：{raw.get('recommended_duration_min', '未知')}分钟\n"
        f"室内景点：{raw.get('indoor', '未知')}\n"
        f"步行强度：{raw.get('walk_level', '未知')}\n"
        f"需要预约：{raw.get('requires_reservation', '未知')}\n"
        f"标签：{tags}"
    )
    return POIDocument(str(raw["id"]), str(raw["name"]), text, metadata)


def load_processed(path: Path = DEFAULT_PROCESSED) -> list[POIDocument]:
    documents: list[POIDocument] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                documents.append(poi_to_document(raw))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid POI at JSONL line {line_number}: {exc}") from exc
    return documents


def load_corpus(path: Path = DEFAULT_CORPUS) -> list[POIDocument]:
    documents: list[POIDocument] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                documents.append(POIDocument.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid corpus line {line_number}: {exc}") from exc
    return documents


def write_corpus(documents: Iterable[POIDocument], path: Path = DEFAULT_CORPUS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for document in documents:
            handle.write(json.dumps(document.to_dict(), ensure_ascii=False) + "\n")


def build_corpus(
    processed_path: Path = DEFAULT_PROCESSED,
    corpus_path: Path = DEFAULT_CORPUS,
) -> int:
    documents = load_processed(processed_path)
    write_corpus(documents, corpus_path)
    return len(documents)
