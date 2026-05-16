#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: embedder
embedding 文本-> 向量

核心问题：文字是离散符号，无法直接比较"The nurse"和"The doctor"有多相似。
嵌入模型把每段文字压缩成一个固定维度的浮点向量，语义越相近的文字，
向量在空间中越靠近。

后端策略（自动切换，接口完全一致）：
  SBERT 模式   — Sentence-BERT，语义准确，需要下载模型（~80MB）
  本地哈希模式  — 纯本地，无需网络，语义近似，用于离线调通管道
"""

import sys
import hashlib
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EMBEDDING_MODEL, EMBEDDING_DIM

try:
    from sentence_transformers import SentenceTransformer

    _SBERT_AVAILABLE = True
except ImportError:
    _SBERT_AVAILABLE = False


class _HashEmbedder:
    """
    把每个词哈希到向量空间，再做平均池化
    相同词-> 相同子向量，共享词汇越多相似度越高。
    纯 numpy,无需网络。
    """

    def __init__(self, dim: int):
        self.dim = dim

    def _word_vec(self, word: str) -> np.ndarray:
        seed = int(hashlib.md5(word.lower().encode()).hexdigest(), 16) % (2 ** 32)
        return np.random.RandomState(seed).randn(self.dim).astype(np.float32)

    def encode(self, texts: list, **_) -> np.ndarray:
        result = []
        for text in texts:
            words = text.lower().split()
            if not words:
                result.append(np.zeros(self.dim, dtype=np.float32))
                continue
            vecs = np.stack([self._word_vec(w) for w in words])
            avg = vecs.mean(axis=0)
            norm = np.linalg.norm(avg)
            result.append(avg / norm if norm > 0 else avg)

        return np.stack(result).astype(np.float32)


class Embedder:
    """
    统一对外的文本嵌入器，上层模块不关心底层后端。
        核心方法：
      encode(texts)        → ndarray (N, dim)，已归一化
      encode_one(text)     → ndarray (dim,)
      cosine_similarity()  → float [-1, 1]
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL, force_local: bool = False):
        self.dim = EMBEDDING_DIM

        if _SBERT_AVAILABLE and not force_local:
            try:
                print(f"[embedder] 加载 Sentence-BERT: {model_name} ...")
                self._backend = SentenceTransformer(model_name)
                self._mode = "sbert"
                print(f"[embedder] SBERT 就绪，向量维度:{self.dim} ")
            except Exception as e:
                print("[embedder] SBERT 加载失败 ({e}), 降级到本地哈希")
                self._backend = _HashEmbedder(self.dim)
                self._mode = "local"
        else:
            print(f"[embedder] 本地哈希模式（维度={self.dim}）")
            self._backend = _HashEmbedder(self.dim)
            self._mode = "local"

    def encode(self, texts: list, show_progress: bool = False) -> np.ndarray:
        """
        编码文本列表 -> (N,dim) float32 已 L2归一化
        归一化后，余弦相似度 = 点积 -> FAISS indexFlatIp 可直接用
        """
        if self._mode == "sbert":
            vecs = self._backend.encode(
                texts,
                show_progress_bar=show_progress,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        else:
            vecs = self._backend.encode(texts)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            vecs = vecs / norms

        return vecs.astype(np.float32)

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    def cosine_similarity(self, text_a: str, text_b: str) -> float:
        """点积 = 余弦相似度（已归一化），范围 [-1,1] """
        return float(np.dot(self.encode_one(text_a), self.encode_one(text_b)))

    @property
    def mode(self) -> str:
        return self._mode


def test():
    emb = Embedder()
    print(f"运行模式:{emb.mode}")

    texts = [
        "The nurse prepared their notes.",
        "A firefighter rushed to the scene.",
        "The weather today is sunny.",
    ]

    vecs = emb.encode(texts)

    print(f"向量矩阵 shape:{vecs.shape}")
    print(f"第一向量 L2 范数: {np.linalg.norm(vecs[0]):.6f}  ← 应约为 1.0")

    print("-语义相似度-")
    pairs = [
        ("The nurse took care of the patient.",
         "The healthcare worker attended to the patient.",
         "语义近 → 分数应高"),
        ("The nurse took care of the patient.",
         "The stock market dropped significantly today.",
         "语义远 → 分数应低"),
        ("The chairman presented his report.",
         "The chairperson presented their report.",
         "性别替换 → 分数应高"),
    ]

    for a, b, label in pairs:
        score = emb.cosine_similarity(a, b)
        print(f"{label}")
        print(f"A:{a}")
        print(f"B:{b}")
        print(f"similarity:{score:.4f}")
    pass


def main():
    test()


if __name__ == "__main__":
    main()
