#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: index_store
FAISS索引的建立，保存，加载

FAISS 是 meta 开源的向量检索库
它能在ms内从大量赂量中找到最相似 的K个，这是RAG检索速度的来源

这个文件做三件事：
    build()-拿向量和chunk文本建索引
    save() - 索引+文本存磁盘
    search()- 给一个查询向量，返回最相似的 top-k 条

IndexFlatIP 的含义
Flat 暴力精确搜索，适合 <10 w 条的小语料
IP  inner Product 内积 余弦相似度（向量已归一化的前提下）

"""
from dataclasses import dataclass

import numpy as np

import faiss
import pickle

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import INDEX_DIR, EMBEDDING_DIM


@dataclass
class SearchResult:
    """检索结果，比祼tuple更清晰"""
    text: str
    source: str
    score: float  # 余弦相似度，越高越相关
    rank: int  # 排名，从 1 开始


class IndexStore:
    """
    FAISS索引 + Chunk文本的封装
    FAISS只存向量，不存原始文本，所以我们同时维护一个list 做映射：
     self.chunks[i] <-> index 里第 i 个向量
    """

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: list[dict] = []

    def build(self, chunks: list, vectors: np.ndarray) -> None:
        """把 chunk 列表和对应向量存入索引"""
        assert len(chunks) == len(vectors), \
            f"chunks({len(chunks)}) 与 vectors({len(vectors)}) 数量不匹配"
        assert vectors.shape[1] == self.dim, \
            f"向量维度 {vectors.shape[1]} != 期望 {self.dim}"

        self.index.add(vectors.astype(np.float32))

        self.chunks = [{"text": c.text, "source": c.source} for c in chunks]
        print(f"[index_store]索引建立完成，共{self.index.ntotal}个向量")

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        """
        用查询向量找最相似的 top_k条
        FAISS 要求输入是 2D：(1, dim)，返回 scores 和 indices 各一行。
        """
        q = query_vec.astype(np.float32).reshape(1, -1)
        scores, indices = self.index.search(q, top_k)

        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            results.append(SearchResult(
                text=chunk["text"],
                source=chunk["source"],
                score=float(score),
                rank=rank,
            ))
        return results

    def save(self, name: str = "corpus") -> None:
        """索引用 FAISS官方格式 存(.faiss), 文本用 pickle(.pkl)"""
        faiss.write_index(self.index, str(INDEX_DIR / f"{name}.faiss"))

        with open(INDEX_DIR / f"{name}_chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)
        print(f"[index_store] 已保存 → {INDEX_DIR}/{name}.faiss / .pkl")

    def load(self, name: str = "corpus") -> None:
        """从磁租恢复索引，跳过重新嵌入"""
        index_path = INDEX_DIR / f"{name}.faiss"
        if not index_path.exists():
            raise FileNotFoundError(f"找不到 {index_path}，请先运行 build()")

        self.index = faiss.read_index(str(index_path))
        with open(INDEX_DIR / f"{name}_chunks.pkl", "rb") as f:
            self.chunks = pickle.load(f)
        print(f"[index_store] 已加载，共 {self.index.ntotal} 个向量")

    @property
    def size(self) -> int:
        return self.index.ntotal


def test():
    from embedder import Embedder
    from dataclasses import dataclass as dc

    @dc
    class FakeChunk:
        text: str
        source: str
        chunk_id: int = 0
        start_char: int = 0

    sample_chunks = [
        FakeChunk("The nurse attended to every patient with care.", "doc_0"),
        FakeChunk("The chairperson opened the board meeting promptly.", "doc_1"),
        FakeChunk("Every firefighter must complete safety training.", "doc_2"),
        FakeChunk("The programmer debugged their code late at night.", "doc_3"),
        FakeChunk("A police officer should respect the rights of all.", "doc_4"),
        FakeChunk("The teacher prepared their lesson plan for the week.", "doc_5"),
    ]

    emb = Embedder()
    vecs = emb.encode([c.text for c in sample_chunks])

    store = IndexStore()
    store.build(sample_chunks, vecs)

    query = "A healthcare worker looked after patients."
    q_vec = emb.encode_one(query)

    print(f"query:{query}")
    print("-top-3 检索结果  ")

    for r in store.search(q_vec, top_k=3):
        print(f"  #{r.rank}  score={r.score:.4f}  [{r.source}]  {r.text}")

    store.save("test")
    store2 = IndexStore()
    store2.load("test")

    print("重新加载后索引大小: {store2.size}")


def main():
    test()


if __name__ == "__main__":
    main()
