#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: retriever

对外统一检索接口(Facade)
上层模块 rag 只调用这一个文件，不关于 embedder,index_store的细节
两个核心方法
build_from_corpus() 第一次运行：语料-> 嵌入 -> 建索引 -> 存盘
retrieve(query,k) 日常使用: 输入文字 -> 返回 top-k 相关 chunk
"""
import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TOP_K, INDEX_DIR

from embedder import Embedder
from index_store import IndexStore, SearchResult


def _load(name: str, subdir: str):
    """
    动态加载带数字前缀目录里的模块。

    注意：把目标 subdir 插到 sys.path 最前面，避免被 site-packages 里的
    同名第三方包劫持（例如 m02_corpus/loader.py vs pip 安装的 `loader` 包）。
    """
    target_dir = Path(__file__).parent.parent / subdir
    target_dir_str = str(target_dir)
    if target_dir_str not in sys.path:
        sys.path.insert(0, target_dir_str)

    spec = importlib.util.spec_from_file_location(
        name, target_dir / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Retriever:
    """
    Embedder + IndexStore 组合体，向上只暴露 retrieve().
    生命周期：
    第一次： retriever().build_from_corpus() 建库并存盘
    之后    retriever().load()
    """

    def __init__(self, index_name: str = "corpus"):
        self.index_name = index_name
        self.embedder = Embedder()
        self.store = IndexStore()
        self._ready = False

    def _index_files(self) -> list[Path]:
        """返回该索引相关的所有落盘文件（用于检测存在性与清理）。"""
        stem = INDEX_DIR / self.index_name
        return [
            Path(f"{stem}.faiss"),
            Path(f"{stem}.pkl"),
            Path(f"{stem}.meta.json"),
        ]

    def build_from_corpus(self,
                          use_builtin: bool = True,
                          strategy: str = "sentence",
                          force_rebuild: bool = False,
                          ) -> None:
        """
        corpus -> clean -> chunk -> embed -> index->save
        force_rebuild = False: 索引已存在时直接加载，不重复嵌入
        """
        index_path = INDEX_DIR / f"{self.index_name}.faiss"

        if index_path.exists() and not force_rebuild:
            print("[retriever] 检测到已有索引，直接加载(跳过重新嵌入)")
            self.load()
            return

        # 强制重建时，清理旧索引相关文件，避免新旧 metadata 不一致
        if force_rebuild:
            for f in self._index_files():
                if f.exists():
                    print(f"[retriever] 清理旧索引文件: {f.name}")
                    f.unlink()

        print("[retriever] step 1: build corpus...")
        corpus_builder = _load("corpus_builder", "m02_corpus")
        chunks = corpus_builder.build_corpus(
            use_builtin=use_builtin,
            strategy=strategy,
            save=True,
        )

        print(f"[retriever] step 2: embedding {len(chunks)} 个 chunk...")
        vectors = self.embedder.encode(
            [c.text for c in chunks], show_progress=True
        )

        print("[retriever] step 3: 建立 FAISS 索引...")
        self.store.build(chunks, vectors)
        self.store.save(self.index_name)

        self._ready = True
        print("[retriever] 建库完成")

    def load(self) -> None:
        self.store.load(self.index_name)
        self._ready = True

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[SearchResult]:
        """
        核心检索接口
        query-> vector -> FAISS近邻搜索-> top-k SearchResult
        """
        if not self._ready:
            raise RuntimeError("检索器未就绪，请先调用 build_from_corpus() 或 load()")

        q_vec = self.embedder.encode_one(query)
        return self.store.search(q_vec, top_k=top_k)

    def retrieve_texts(self, query: str, top_k: int = TOP_K) -> list[str]:
        """只返回文本列表，方便直接拼进 prompt"""
        return [r.text for r in self.retrieve(query, top_k)]


def test():
    # 建库（索引已存在则自动跳过）
    retriever = Retriever()
    retriever.build_from_corpus(use_builtin=True, strategy="sentence")

    # 模拟论文场景：输入有偏见的句子，检索包容性参考
    test_queries = [
        "The chairman should inform his employees about the policy.",
        "The policeman caught the criminal and filed his report.",
        "The nurse helped the patient and she was very professional.",
        "Every programmer must test his code before deployment.",
    ]

    print("\n" + "=" * 60)
    print("  检索测试：有偏见输入 → 包容性参考")
    print("=" * 60)

    for query in test_queries:
        print(f"{query}")
        for r in retriever.retrieve(query, top_k=3):
            print(f"   #{r.rank} [{r.score:.4f}] {r.text}")


def main():
    test()


if __name__ == "__main__":
    main()