#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: two_pass
把 first pass 和 second pass串联起来，是 m4_rag 对外的唯一入口

调用方：m7_pipeline 和 实验脚本只需要
from m4_rag.two_pass import twopassRag
rag = TwoPassRag(retriever)
对外隐藏两次检索和两次LLM调用的细节
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util


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



_fp_mod = _load("first_pass", "m04_rag")
_sp_mod = _load("second_pass", "m04_rag")


class TwoPassRAG:
    """
    论文核心架构的 python 实现
      │ 原文（有偏见）                           │
      │   ↓ retrieve（用原文查）                 │
      │   ↓ LLM（First Pass prompt）            │
      │ 初步去偏版本                             │
      │   ↓ retrieve（用去偏版本查）             │
      │   ↓ LLM（Second Pass prompt）           │
      │ 最终精炼版本
    """

    def __init__(self, retriever, top_k: int = 5):
        self.retriever = retriever
        self.top_k = top_k

    def run(self, text: str, verbose: bool = False) -> dict:
        """
        对一段文字执行完整的 two-pass RAG.
        返回包含完整过程的dict
        original 输入原文
        first_pass first pass 的完整结果 dict
        second_pass  second pass 的完整结果
        final_output 最终输出
        """
        if verbose:
            print(f"[two_pass]原文: {text}")
        # first pass
        fp_result = _fp_mod.first_pass(text, self.retriever, top_k=self.top_k)

        if verbose:
            print(f"[two pass] first pass -> result:{fp_result['output']} ")

        # second pass
        sp_result = _sp_mod.second_pass(
            original=text,
            first_pass_output=fp_result["output"],
            retriever=self.retriever,
            top_k=self.top_k,
        )
        if verbose:
            print(f"[two pass] second pass -> result:{sp_result['output']}")

        return {
            "original": text,
            "first_pass": fp_result,
            "second_pass": sp_result,
            "final_output": sp_result['output'],
        }

    def run_batch(self, texts: list[str], verbose: bool = False) -> list[dict]:
        return [self.run(t, verbose=verbose) for t in texts]


def print_result(result: dict) -> None:
    """格式化打印单条结果，方便实验对比。"""
    print(f"\n{'═' * 60}")
    print(f"  原文       : {result['original']}")
    print(f"  First Pass : {result['first_pass']['output']}")
    print(f"  Final      : {result['final_output']}")
    print(f"{'═' * 60}")
    print(f"  ── First Pass 检索参考 ──")
    for i, ref in enumerate(result['first_pass']['references'][:2], 1):
        print(f"  [{i}] {ref}")
    print(f"  ── Second Pass 检索参考 ──")
    for i, ref in enumerate(result['second_pass']['references'][:2], 1):
        print(f"  [{i}] {ref}")


def test():
    # 初始化检索器
    retriever_mod = _load("retriever", "m03_embeddings")
    retriever = retriever_mod.Retriever()
    retriever.build_from_corpus(use_builtin=True)

    rag = TwoPassRAG(retriever, top_k=3)

    # 论文中的典型测试用例
    test_inputs = [
        "The chairman must update his staff on the new company policy.",
        "Each policeman should submit his report before the end of his shift.",
        "The nurse said she would check on the patient after her break.",
        "Every businessman needs to review his contracts carefully.",
        "The fireman rushed into the building to save the victims.",
    ]

    print("\n" + "=" * 60)
    print("  Two-Pass RAG — 完整流水线测试")
    print("=" * 60)

    results = rag.run_batch(test_inputs)
    for r in results:
        print_result(r)

    print()


def main():
    test()


if __name__ == "__main__":
    main()
