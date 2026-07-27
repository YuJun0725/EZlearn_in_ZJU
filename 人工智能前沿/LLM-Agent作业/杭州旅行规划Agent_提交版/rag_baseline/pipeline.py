from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .documents import DEFAULT_CORPUS, DEFAULT_PROCESSED, build_corpus
from .llm import RAGLLMClient, RAGLLMError
from .narrative import format_rag_natural_language
from .retriever import BM25Retriever


class RAGBaselineError(RuntimeError):
    pass


class RAGBaseline:
    """RAG-only comparison pipeline; it deliberately skips the main planner."""

    def __init__(self, corpus_path: Path = DEFAULT_CORPUS) -> None:
        if not corpus_path.is_file():
            build_corpus(DEFAULT_PROCESSED, corpus_path)
        self.retriever = BM25Retriever.from_corpus(corpus_path)

    def run(self, user_text: str, *, top_k: int = 5, generate: bool = True) -> dict[str, Any]:
        text = user_text.strip()
        if not text:
            raise RAGBaselineError("旅行需求不能为空")
        retrieve_started = time.perf_counter()
        retrieved = self.retriever.search(text, top_k=top_k)
        retrieve_ms = (time.perf_counter() - retrieve_started) * 1000
        payload: dict[str, Any] = {
            "status": "retrieved",
            "mode": "rag_baseline",
            "query": text,
            "top_k": top_k,
            "retrieved": [item.to_dict() for item in retrieved],
            "retrieval_ms": round(retrieve_ms, 2),
            "answer": None,
            "natural_language_output": None,
            "generation_ms": None,
            "errors": [],
        }
        if not generate:
            payload["natural_language_output"] = format_rag_natural_language(payload)
            return payload
        generation_started = time.perf_counter()
        try:
            answer = RAGLLMClient.from_env().generate(text, retrieved)
        except RAGLLMError as exc:
            payload["status"] = "failed"
            payload["errors"] = [str(exc)]
            payload["natural_language_output"] = format_rag_natural_language(payload)
            return payload
        payload["status"] = "completed"
        payload["answer"] = answer
        payload["natural_language_output"] = format_rag_natural_language(payload)
        payload["generation_ms"] = round((time.perf_counter() - generation_started) * 1000, 2)
        return payload
