from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from typing import Iterable, List


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class KnowledgeChunk:
    doc_id: str
    title: str
    text: str


@dataclass
class AgentResult:
    intent: str
    tool_trace: List[str]
    answer: str
    citations: List[str]


class SimpleRAG:
    def __init__(self, chunks: Iterable[KnowledgeChunk]) -> None:
        self.chunks = list(chunks)

    @staticmethod
    def _tokens(text: str) -> set[str]:
        lowered = text.lower()
        ascii_tokens = set(re.findall(r"[a-z0-9_]+", lowered))
        chinese_terms = {
            term
            for term in [
                "大模型",
                "语言模型",
                "智能体",
                "agent",
                "rag",
                "工具",
                "知识库",
                "测试",
                "评估",
                "学习计划",
                "课程",
                "作业",
                "架构",
                "训练",
                "应用",
                "拆解",
                "决策",
                "客服",
                "问答",
            ]
            if term in lowered
        }
        chars = {ch for ch in lowered if "\u4e00" <= ch <= "\u9fff"}
        return ascii_tokens | chinese_terms | chars

    def retrieve(self, query: str, top_k: int = 3) -> List[KnowledgeChunk]:
        query_tokens = self._tokens(query)
        lowered_query = query.lower()
        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk in self.chunks:
            chunk_tokens = self._tokens(chunk.title + " " + chunk.text)
            overlap = query_tokens & chunk_tokens
            boost = self._domain_boost(lowered_query, chunk.doc_id)
            if not overlap and boost == 0:
                continue
            score = len(overlap) / (len(query_tokens) + 1) + boost
            scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    @staticmethod
    def _domain_boost(query: str, doc_id: str) -> float:
        rules = {
            "K1": ["llm", "大模型", "语言模型"],
            "K2": ["agent", "智能体", "拆解", "决策"],
            "K3": ["rag", "知识库", "检索", "幻觉"],
            "K4": ["工具", "skill", "调用"],
            "K5": ["评估", "评价", "测试", "正确率", "命中率"],
        }
        return 2.0 if any(keyword in query for keyword in rules[doc_id]) else 0.0


class MockLLM:
    def generate(self, query: str, evidence: List[KnowledgeChunk], intent: str) -> str:
        evidence_text = "；".join(f"{item.title}: {item.text}" for item in evidence)
        if intent == "plan":
            return (
                "可以按“需求理解-资料检索-任务拆解-结果生成-自检优化”的流程完成。"
                "第一步整理课程要求和资料，第二步用知识库检索相关内容，第三步由 Agent 拆成问答、计划、测试等子任务，"
                "最后生成带引用的答案并检查是否覆盖作业要求。依据：" + evidence_text
            )
        if intent == "quiz":
            return (
                "可生成三类练习：概念题考察 LLM 和 Agent 区别，设计题考察 RAG 与工具调用，"
                "评价题考察正确率、引用一致性和用户满意度。依据：" + evidence_text
            )
        return (
            "本系统将大语言模型作为自然语言理解与生成模块，将 Agent 作为任务控制模块。"
            "Agent 先识别用户意图，再调用知识库检索、学习计划、练习生成等工具，最后由语言模型整合回答。"
            "依据：" + evidence_text
        )


class CourseAgent:
    def __init__(self, rag: SimpleRAG, llm: MockLLM) -> None:
        self.rag = rag
        self.llm = llm

    @staticmethod
    def classify_intent(query: str) -> str:
        if any(word in query for word in ["计划", "步骤", "怎么学", "思路", "安排"]):
            return "plan"
        if any(word in query for word in ["练习", "测试题", "自测", "题目"]):
            return "quiz"
        return "qa"

    def answer(self, query: str) -> AgentResult:
        trace: list[str] = []
        intent = self.classify_intent(query)
        trace.append(f"classify_intent -> {intent}")

        evidence = self.rag.retrieve(query, top_k=3)
        trace.append("retrieve -> " + ", ".join(item.doc_id for item in evidence))

        response = self.llm.generate(query, evidence, intent)
        trace.append("generate -> mock_llm")

        return AgentResult(
            intent=intent,
            tool_trace=trace,
            answer=response,
            citations=[item.doc_id for item in evidence],
        )


def build_agent() -> CourseAgent:
    chunks = [
        KnowledgeChunk(
            "K1",
            "LLM 基础",
            "大语言模型通常基于 Transformer 架构，通过预训练、指令微调和人类反馈对齐获得语言理解与生成能力。",
        ),
        KnowledgeChunk(
            "K2",
            "Agent 基础",
            "智能体负责目标理解、任务拆解、决策、记忆管理和工具调用，可把复杂需求拆成可执行步骤。",
        ),
        KnowledgeChunk(
            "K3",
            "RAG 设计",
            "RAG 通过向量检索或关键词检索从知识库召回依据，再把证据交给语言模型生成答案，能降低幻觉。",
        ),
        KnowledgeChunk(
            "K4",
            "工具与 Skill",
            "Skill 是可复用能力单元，例如课程问答、学习计划、练习生成和答案自检；工具用于检索、计算或格式化输出。",
        ),
        KnowledgeChunk(
            "K5",
            "评估方法",
            "系统可从意图识别准确率、检索命中率、答案正确率、引用一致性、流畅度和响应时间等维度评估。",
        ),
    ]
    return CourseAgent(SimpleRAG(chunks), MockLLM())


def run_demo() -> None:
    agent = build_agent()
    samples = [
        "LLM 和 Agent 在课程学习助手中分别负责什么？",
        "请给我一个完成 LLM Agent 作业的思路和步骤",
        "围绕 RAG 和工具调用生成几道自测题目",
    ]
    for query in samples:
        result = agent.answer(query)
        print("=" * 72)
        print("用户问题:", query)
        print("识别意图:", result.intent)
        print("调用轨迹:", " | ".join(result.tool_trace))
        print("引用来源:", ", ".join(result.citations))
        print("回答:", result.answer)


def evaluate() -> None:
    agent = build_agent()
    tests = [
        ("LLM 和 Agent 分工是什么？", "qa", lambda r: "K1" in r.citations and "K2" in r.citations),
        ("给我完成作业的整体思路", "plan", lambda r: "K2" in r.citations),
        ("帮我生成测试题目", "quiz", lambda r: "K5" in r.citations or "K4" in r.citations),
        ("RAG 为什么能减少幻觉？", "qa", lambda r: "K3" in r.citations),
        ("如何评价这个系统？", "qa", lambda r: "K5" in r.citations),
    ]
    intent_hits = 0
    retrieval_hits = 0
    for query, expected_intent, judge in tests:
        result = agent.answer(query)
        intent_hits += int(result.intent == expected_intent)
        retrieval_hits += int(judge(result))
    total = len(tests)
    print(f"intent_accuracy={intent_hits / total:.2f}")
    print(f"retrieval_hit_rate={retrieval_hits / total:.2f}")
    print("faithfulness_check=answers include explicit citation ids")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline demo for an LLM + Agent course assistant.")
    parser.add_argument("--eval", action="store_true", help="run deterministic evaluation")
    args = parser.parse_args()
    if args.eval:
        evaluate()
    else:
        run_demo()


if __name__ == "__main__":
    main()
