from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .documents import DEFAULT_CORPUS, POIDocument, load_corpus


_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """Tokenize Chinese text with characters and adjacent bigrams."""
    tokens: list[str] = []
    for segment in _TOKEN_RE.findall(text.lower()):
        if all("\u4e00" <= char <= "\u9fff" for char in segment):
            tokens.extend(segment)
            tokens.extend(segment[index : index + 2] for index in range(len(segment) - 1))
        else:
            tokens.append(segment)
    return tokens


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    document: POIDocument
    score: float
    rank: int

    def to_dict(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "score": round(self.score, 4),
            **self.document.to_dict(),
        }


class BM25Retriever:
    """Dependency-free sparse retriever for the small POI comparison corpus."""

    def __init__(self, documents: Iterable[POIDocument]) -> None:
        self.documents = tuple(documents)
        if not self.documents:
            raise ValueError("RAG corpus is empty")
        self._token_sets = [Counter(tokenize(doc.text)) for doc in self.documents]
        self._average_length = sum(sum(item.values()) for item in self._token_sets) / len(
            self._token_sets
        )
        document_frequency: Counter[str] = Counter()
        for term_counts in self._token_sets:
            document_frequency.update(term_counts.keys())
        self._idf = {
            term: math.log(1 + (len(self.documents) - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    @classmethod
    def from_corpus(cls, path=DEFAULT_CORPUS) -> BM25Retriever:
        return cls(load_corpus(path))

    def search(self, query: str, top_k: int = 5) -> list[RetrievedDocument]:
        if not query.strip():
            raise ValueError("RAG query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query_terms = Counter(tokenize(query))
        normalized_query = re.sub(r"\s+", "", query)
        scores: list[tuple[float, int]] = []
        k1, b = 1.5, 0.75
        for index, term_counts in enumerate(self._token_sets):
            length = sum(term_counts.values())
            score = 0.0
            for term, query_frequency in query_terms.items():
                frequency = term_counts.get(term, 0)
                if not frequency:
                    continue
                denominator = frequency + k1 * (1 - b + b * length / self._average_length)
                term_score = self._idf.get(term, 0.0) * frequency * (k1 + 1) / denominator
                if query_frequency > 1:
                    term_score *= 1 + min(query_frequency, 3) * 0.03
                score += term_score
            document = self.documents[index]
            if document.name and document.name in normalized_query:
                score += 5.0
            scores.append((score, index))
        scores.sort(key=lambda item: (-item[0], item[1]))
        return [
            RetrievedDocument(self.documents[index], score, rank)
            for rank, (score, index) in enumerate(scores[:top_k], start=1)
        ]
