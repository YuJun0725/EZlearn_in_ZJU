from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import RAGBaseline


def main() -> int:
    parser = argparse.ArgumentParser(description="隔离的轻量 RAG 旅行规划基线")
    parser.add_argument("--text", required=True, help="自然语言旅行需求")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--retrieve-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--natural-language",
        action="store_true",
        help="输出结构化 RAG 结果对应的自然语言说明",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = RAGBaseline().run(args.text, top_k=args.top_k, generate=not args.retrieve_only)
    if args.natural_language:
        rendered = result.get("natural_language_output") or "未生成自然语言说明"
    else:
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] in {"retrieved", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
