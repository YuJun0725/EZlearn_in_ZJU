from __future__ import annotations

import argparse
from pathlib import Path

from .documents import DEFAULT_CORPUS, DEFAULT_PROCESSED, build_corpus


def main() -> int:
    parser = argparse.ArgumentParser(description="构建隔离的 POI RAG 文档语料")
    parser.add_argument("--input", type=Path, default=DEFAULT_PROCESSED)
    parser.add_argument("--output", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()
    count = build_corpus(args.input, args.output)
    print(f"Built {count} POI documents: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
