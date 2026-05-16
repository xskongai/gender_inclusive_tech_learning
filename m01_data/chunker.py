#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/11/26
Description: chunker

m01_data/chunker.py — 文本分块
职责：把长文本切成适合嵌入和检索的小块。

策略：
  - fixed_size_chunks：按字符数切，带重叠窗口（最简单，论文用的也是这类）
  - sentence_chunks：按句子边界切，更自然

"""
import re
from dataclasses import dataclass

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class Chunk:
    text: str
    source: str
    chunk_id: int
    start_char: int


def fixed_size_chunks(
        text: str,
        source: str = "unknown",
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """
    滑动窗口分块。
    chunk_size=200, overlap=40 → 每块 200 字符，相邻块共享 40 字符。
    重叠的作用：避免一个完整句子被切断在两个块的边界处，导致检索时丢失上下文。
    """
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(Chunk(
                text=chunk_text,
                source=source,
                chunk_id=chunk_id,
                start_char=start,
            ))
        chunk_id += 1
        start += chunk_size - overlap

    return chunks


def sentence_chunks(
        text: str,
        source: str = "unknown",
        max_sentences: int = 3,
) -> list[Chunk]:
    """
    按句子边界分块，每块包含 max_sentences 个句子。
    比 fixed_size 更自然，不会在句子中间截断。
    """
    # 简单句子分割：遇到 .!? 后跟空格或结尾就断开
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    for i in range(0, len(sentences), max_sentences):
        group = sentences[i:i + max_sentences]
        chunk_text = " ".join(group)
        chunks.append(
            Chunk(
                text=chunk_text,
                source=source,
                chunk_id=i // max_sentences,
                start_char=-1  # 句子分块不追踪字符位置
            )
        )
    return chunks


def chunk_documents(
        docs: list[dict],
        strategy: str = "fixed",
        **kwargs,
) -> list[Chunk]:
    """批量处理多个文档。"""
    all_chunks = []
    for doc in docs:
        text = doc.get("text", "")
        source = doc.get("source", "unknown")
        if strategy == "fixed":
            all_chunks.extend(fixed_size_chunks(text, source, **kwargs))
        elif strategy == "sentence":
            all_chunks.extend(sentence_chunks(text, source, **kwargs))
        else:
            raise ValueError(f"Unknown strategy:{strategy}")
    return all_chunks


def test():
    sample_text = (
        "The police officer finished his shift and went home. "
        "He had spent the day helping citizens across the city. "
        "The nurse prepared her notes before the next patient arrived. "
        "She carefully reviewed each case in the ward. "
        "Every student should submit their assignments on time. "
        "They are responsible for their own learning journey."
    )

    print("--fixed-size chunks --")
    for c in fixed_size_chunks(sample_text, source="sample", chunk_size=120, overlap=20):
        print(f"[{c.chunk_id}]{repr(c.text)}")

    print("-- sentence chunks -- ")
    for c in sentence_chunks(sample_text, source="sample", max_sentences=2):
        print(f"[{c.chunk_id}]{repr(c.text)}")


def main():
    test()


if __name__ == "__main__":
    main()
