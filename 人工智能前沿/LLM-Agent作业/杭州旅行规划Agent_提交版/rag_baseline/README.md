# 轻量 RAG 对比基线

此目录与主 Agent 隔离，用于课程报告中的 RAG 方案对比，不修改
`src/travel_agent/` 的现有规划逻辑。

## 组成

- `documents.py`：把结构化 POI 转成可检索文本块。
- `retriever.py`：纯 Python BM25 稀疏检索，不依赖向量数据库或第三方包。
- `prompt.py`：将 Top-K POI 和用户需求拼接到 RAG Prompt。
- `llm.py`：调用 OpenAI 兼容接口生成 JSON 行程。
- `pipeline.py`：检索和生成流程；刻意不调用主 Agent 的路线、预算和约束校验。
- `narrative.py`：将 RAG 的结构化 JSON 确定性转换为自然语言说明。
- `data/poi_documents.jsonl`：独立的 RAG 文档语料。

## 运行

首次构建语料：

```powershell
python -m rag_baseline.build_corpus
```

只测试检索，不调用大模型：

```powershell
python -m rag_baseline.run --text "两个人去杭州玩两天，喜欢历史和美术，灵隐寺必去" --retrieve-only
```

运行 RAG + LLM 基线：

```powershell
python -m rag_baseline.run --text "两个人去杭州玩两天，预算1200元，喜欢历史和美术，灵隐寺必去" --top-k 8
```

只显示结构化结果对应的自然语言说明：

```powershell
python -m rag_baseline.run --text "两个人去杭州玩两天，预算1200元，喜欢历史和美术，灵隐寺必去" --top-k 8 --natural-language
```

默认 JSON 输出会同时保留原来的 `answer`，并新增 `natural_language_output` 字段。
自然语言内容由程序根据 JSON 生成，不会再次调用大模型。检索-only 模式也可以加
`--natural-language`，此时输出的是候选 POI 摘要，不是完整行程。

主 Agent 与本基线的差异：RAG 基线只检索文本并交给 LLM 生成，不使用
`ItineraryOptimizer`、`BudgetTool`、路线工具和约束校验器，适合做消融对比。
