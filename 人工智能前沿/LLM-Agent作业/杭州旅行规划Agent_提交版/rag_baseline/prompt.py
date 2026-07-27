from __future__ import annotations

from collections.abc import Iterable

from .retriever import RetrievedDocument


def build_prompt(user_text: str, retrieved: Iterable[RetrievedDocument]) -> str:
    context = "\n\n".join(
        f"[{item.rank}]\n{item.document.text}" for item in retrieved
    )
    return f"""你是杭州旅行规划 RAG 基线模型。请严格只使用下方检索到的 POI，不要编造景点、价格、地址或开放时间。

用户需求：
{user_text.strip()}

检索到的 POI：
{context}

请只输出一个 JSON 对象，格式如下：
{{
  "summary": "一句话概括行程",
  "days": [
    {{
      "day": 1,
      "items": [
        {{"poi_name": "POI名称", "start_time": "09:00", "end_time": "10:30", "reason": "安排理由"}}
      ]
    }}
  ],
  "estimated_total_yuan": 0,
  "assumptions": ["需要说明的不确定信息"]
}}
"""
