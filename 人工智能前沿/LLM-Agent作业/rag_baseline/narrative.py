from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


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


def _contains_name(left: str, right: str) -> bool:
    left = "".join(left.split())
    right = "".join(right.split())
    return bool(left and right and (left in right or right in left))


def _retrieval_summary(payload: Mapping[str, Any]) -> str:
    query = str(payload.get("query", "")).strip()
    retrieved = [_mapping(item) for item in _sequence(payload.get("retrieved"))]
    names = [str(item.get("name", "未命名景点")) for item in retrieved]
    if names:
        text = f"根据“{query}”检索到{len(names)}个候选 POI，优先包括：" + "、".join(names[:5]) + "。"
    else:
        text = f"根据“{query}”暂未检索到候选 POI。"
    if payload.get("status") != "completed":
        text += "当前尚未生成完整的 RAG 行程。"
    else:
        text += "当前仅展示检索结果，尚未调用大模型生成完整行程。"
    return text


def format_rag_natural_language(payload: Mapping[str, Any]) -> str:
    """Render the RAG JSON answer as a user-facing Chinese explanation."""

    answer = _mapping(payload.get("answer"))
    if not answer:
        return _retrieval_summary(payload)

    paragraphs: list[str] = []
    summary = str(answer.get("summary", "")).strip()
    if summary:
        paragraphs.append(summary)

    retrieved_names = [
        str(_mapping(item).get("name", ""))
        for item in _sequence(payload.get("retrieved"))
    ]
    all_items: list[Mapping[str, Any]] = []
    for day in _sequence(answer.get("days")):
        day_data = _mapping(day)
        items = [_mapping(item) for item in _sequence(day_data.get("items"))]
        all_items.extend(items)
        day_number = day_data.get("day", "?")
        if not items:
            paragraphs.append(f"第{day_number}天暂未安排具体景点。")
            continue
        descriptions: list[str] = []
        for item in items:
            name = str(item.get("poi_name", "未命名景点"))
            start = str(item.get("start_time", ""))
            end = str(item.get("end_time", ""))
            time_text = f"{start}-{end} " if start and end else ""
            reason = str(item.get("reason", "")).strip()
            reason_text = f"（{reason}）" if reason else ""
            descriptions.append(f"{time_text}{name}{reason_text}")
        paragraphs.append(f"第{day_number}天安排：" + "，随后".join(descriptions) + "。")

    total = _money(answer.get("estimated_total_yuan"))
    if total:
        paragraphs.append(f"模型给出的预计总费用为{total}。该金额仅为 RAG 生成结果，未经过主 Agent 的预算工具复核。")

    assumptions = [str(item).strip() for item in _sequence(answer.get("assumptions")) if str(item).strip()]
    if assumptions:
        paragraphs.append("需要注意：" + "；".join(assumptions) + "。")

    generated_names = [
        str(item.get("poi_name", ""))
        for item in all_items
        if str(item.get("poi_name", "")).strip()
    ]
    grounded_count = sum(
        any(_contains_name(name, retrieved) for retrieved in retrieved_names)
        for name in generated_names
    )
    if generated_names:
        paragraphs.append(
            f"本次生成的{len(generated_names)}个景点中，有{grounded_count}个可以在检索到的 POI 文档中找到，"
            "该比例仅用于衡量知识库依据程度，不代表预算、路线和开放时间已经完成校验。"
        )
    return "\n".join(paragraphs)

