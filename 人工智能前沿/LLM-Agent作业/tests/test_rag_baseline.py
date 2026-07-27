from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_baseline.documents import DEFAULT_CORPUS, load_corpus  # noqa: E402
from rag_baseline.narrative import format_rag_natural_language  # noqa: E402
from rag_baseline.pipeline import RAGBaseline  # noqa: E402
from rag_baseline.prompt import build_prompt  # noqa: E402
from rag_baseline.retriever import BM25Retriever, tokenize  # noqa: E402


class RAGBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = load_corpus(DEFAULT_CORPUS)
        cls.retriever = BM25Retriever(cls.documents)

    def test_isolated_corpus_contains_current_pois(self) -> None:
        self.assertEqual(len(self.documents), 69)
        self.assertEqual(len({item.id for item in self.documents}), 69)

    def test_retrieves_must_visit_poi_in_top_k(self) -> None:
        results = self.retriever.search("灵隐寺必去，喜欢历史", top_k=5)
        names = [item.document.name for item in results]
        self.assertTrue(any("灵隐寺" in name for name in names))

    def test_chinese_tokenizer_keeps_unigrams_and_bigrams(self) -> None:
        terms = tokenize("杭州美术馆")
        self.assertIn("杭", terms)
        self.assertIn("杭州", terms)
        self.assertIn("美术", terms)

    def test_retrieval_only_pipeline_does_not_call_llm(self) -> None:
        result = RAGBaseline(DEFAULT_CORPUS).run(
            "杭州一日游，喜欢历史和美术",
            top_k=4,
            generate=False,
        )
        self.assertEqual(result["status"], "retrieved")
        self.assertEqual(len(result["retrieved"]), 4)
        self.assertIsNone(result["answer"])
        self.assertIn("检索到", result["natural_language_output"])

    def test_prompt_contains_retrieved_facts(self) -> None:
        results = self.retriever.search("灵隐寺", top_k=2)
        prompt = build_prompt("灵隐寺必去", results)
        self.assertIn("灵隐寺", prompt)
        self.assertIn("成人票价", prompt)
        self.assertIn("只输出一个 JSON 对象", prompt)

    def test_rag_answer_can_be_rendered_as_natural_language(self) -> None:
        rendered = format_rag_natural_language(
            {
                "status": "completed",
                "query": "灵隐寺必去",
                "retrieved": [{"name": "灵隐寺"}],
                "answer": {
                    "summary": "杭州历史文化游",
                    "days": [
                        {
                            "day": 1,
                            "items": [
                                {
                                    "poi_name": "灵隐寺",
                                    "start_time": "09:00",
                                    "end_time": "10:30",
                                    "reason": "满足必去要求",
                                }
                            ],
                        }
                    ],
                    "estimated_total_yuan": 100,
                    "assumptions": ["交通费用未核验"],
                },
            }
        )
        self.assertIn("杭州历史文化游", rendered)
        self.assertIn("第1天安排", rendered)
        self.assertIn("灵隐寺", rendered)
        self.assertIn("知识库依据程度", rendered)


if __name__ == "__main__":
    unittest.main()
