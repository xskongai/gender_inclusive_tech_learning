#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: corpus_builder

语料加工
职责：
1.调用 loader 取原始文档
2.调用01_data 的 cleaner+chunker 加工成 chunk列表
3.把加工好的 chunk 序列化保存，供03_embeddings 使用

这是 01 和 03 之间的桥梁
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATA_PROCESSED, CHUNK_SIZE, CHUNK_OVERLAP
from loader import load_all

# 注意：因为目录名带数字前缀，直接 import 会报错。
# 实际运行时我们用 sys.path + importlib 绕过，见 _import_data_module()
import importlib, types


def _get_data_module(name: str):
    """动态导入带数字前缀的模块（m01_data.xxx）。"""
    spec = importlib.util.spec_from_file_location(
        name,
        Path(__file__).parent.parent / "m01_data" / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cleaner = _get_data_module("cleaner")
_chunker = _get_data_module("chunker")

Chunk = _chunker.Chunk  # 从动态加载的模块取 Chunk 类型


def build_corpus(
        txt_paths: list | None = None,
        xlsx_paths: list | None = None,
        use_builtin: bool = True,
        strategy: str = "sentence",  # "fixed" | "sentence"
        chunk_size: int = CHUNK_SIZE,
        overlap: int = CHUNK_OVERLAP,
        save: bool = True,
) -> list[Chunk]:
    """
    完整的语料构建流水线
    load -> clean -> chunk -> save -> return chunks
    """
    print("[corpus_builder] step 1 :load original docs...")
    docs = load_all(
        txt_paths=txt_paths,
        xlsx_paths=xlsx_paths,
        use_builtin=use_builtin,
    )
    print("[corpus_builder] step 2 : clean text...")
    for doc in docs:
        doc["text"] = _cleaner.clean(doc["text"])
    # 过滤清洗后变空的文档
    docs = [d for d in docs if d["text"].strip()]
    print(f"->清洗后 剩余{len(docs)}条")

    print("[corpus_builder] step 3 : chunk...")
    if strategy == "fixed":
        chunks = _chunker.chunk_documents(
            docs, strategy="fixed",
            chunk_size=chunk_size,
            overlap=overlap,
        )
    else:
        chunks = _chunker.chunk_documents(
            docs, strategy="sentence", max_sentences=2
        )
    print(f"->共生成{len(chunks)} 个 chunk")

    print("[corpus_builder] step 4 : remove duplicated...")
    seen = set()
    unique_chunks = []
    for c in chunks:
        if c.text not in seen:
            seen.add(c.text)
            unique_chunks.append(c)
    print("->去重后 剩余{len(unique_chunks)}个 chunk")

    if save:
        _save_chunks(unique_chunks)

    return unique_chunks


def _save_chunks(chunks: list[Chunk]) -> Path:
    """把Chunk序列化为JSON,供03_embeddings加载."""
    out_path = DATA_PROCESSED / "corpus_chunks.json"
    data = [
        {
            "text": c.text,
            "source": c.source,
            "chunk_id": c.chunk_id,
            "start_char": c.start_char,
        }
        for c in chunks
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[corpus_builder] 已保存在{out_path}")
    return out_path


def load_saved_chunks() -> list[Chunk]:
    path = DATA_PROCESSED / "corpus_chunks.json"
    if not path.exists():
        raise FileNotFoundError(
            "找不到已保存的语料，请先运行build_corpus()"
        )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [
        Chunk(
            text=d["text"],
            source=d["source"],
            chunk_id=d["chunk_id"],
            start_char=d["start_char"],
        )
        for d in data
    ]


def test():
    chunks = build_corpus(use_builtin=True, strategy="sentence", save=True)

    print("前5个chunk示例：")
    for c in chunks[:5]:
        print(f"  [{c.source} | chunk_{c.chunk_id}]")
        print(f"  {repr(c.text)}")
        print()

    print("check reload from disk")
    reloaded = load_saved_chunks()
    print(f"重新加载:{len(reloaded)}个Chunk ")


def main():
    test()


if __name__ == "__main__":
    main()
