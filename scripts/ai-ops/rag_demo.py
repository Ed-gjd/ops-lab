#!/usr/bin/env python3
"""
课5：RAG 演示 —— 解析->分片->向量->检索->生成 全链路
知识库 = ops_kb.md（你真环境的事实，模型本来不可能知道）
用法：RAG_THRESHOLD=0.3 python rag_demo.py "问题1" "问题2"
"""
import math
import os
import sys

from openai import OpenAI

import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from paths import CC, WIN_ROOT, VENV_PY

client = OpenAI(api_key=os.environ["DASHSCOPE_API_KEY"],
                base_url=os.environ["DASHSCOPE_BASE_URL"])
EMB = "qwen3.7-text-embedding"
LLM = os.environ.get("L3_MODEL", "qwen-plus")
THRESHOLD = float(os.environ.get("RAG_THRESHOLD", "0.3"))  # 相似度阈值（练习2 调它）
KB = f"{CC}/agent/ops_kb.md"


def embed(texts):
    r = client.embeddings.create(model=EMB, input=texts)
    return [d.embedding for d in r.data]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0


def load_kb(path):
    return [c.strip() for c in open(path).read().split("\n\n") if c.strip()]


def ask(question, chunks, vecs):
    qv = embed([question])[0]
    scored = sorted(((cosine(qv, v), i) for i, v in enumerate(vecs)), reverse=True)
    hits = [(s, chunks[i]) for s, i in scored[:2] if s >= THRESHOLD]
    print(f"[检索] 最高相似度 {scored[0][0]:.3f}（阈值 {THRESHOLD}）→ 命中 {len(hits)} 块")
    for s, c in hits:
        print(f"   相似度 {s:.3f} | {c[:40]}...")
    if not hits:
        print("[生成] 无命中 → 严格防幻觉分支")
        r = client.chat.completions.create(model=LLM, messages=[
            {"role": "system", "content": "你是运维知识助手，只依据知识库回答。知识库未覆盖时，只能回复一句话：'知识库未覆盖该问题'，禁止补充任何推测、常识或建议。"},
            {"role": "user", "content": f"问题：{question}"}])
        print(f"[回答] {r.choices[0].message.content}\n")
        return
    context = "\n---\n".join(c for _, c in hits)
    r = client.chat.completions.create(model=LLM, messages=[
        {"role": "system", "content": "你是运维知识助手。只依据下面知识库内容回答，未覆盖则明说。"},
        {"role": "user", "content": f"知识库：\n{context}\n\n问题：{question}"}])
    print(f"[回答] {r.choices[0].message.content}\n")


if __name__ == "__main__":
    chunks = load_kb(KB)
    print(f"== 知识库分块: {len(chunks)} 块 ==")
    vecs = embed(chunks)  # 入库：全部转向量
    qs = sys.argv[1:] or ["node3 是什么角色、IP 多少？"]
    for q in qs:
        print(f">>> 问：{q}")
        ask(q, chunks, vecs)
