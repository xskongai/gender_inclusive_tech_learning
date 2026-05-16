#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/16/26
Description: cot_rag

cot + two-pass RAG 结合
把 m04_rag 的两次检索和 m05_cot 的 逐步推理合并

流程：
原文
retrieve first pass
cot prompt 包括 参考 + 推理步骤
初步去偏输出+ 推理链
retrieve second pass 用去偏版本查
cot prompt
最终输出+完整推理记录

对比
two_pass 直接改写，无推理过程
cot_rag  有推理过程，可解释，漏改的偏见词更少
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TOP_K

import importlib.util


def _load(name: str, subdir: str):
    project_root = Path(__file__).resolve().parents[1]
    target_dir = project_root / subdir

    target_dir_str = str(target_dir)
    if target_dir_str in sys.path:
        sys.path.remove(target_dir_str)
    sys.path.insert(0, target_dir_str)

    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    spec = importlib.util.spec_from_file_location(
        name,
        target_dir / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_cot_chain = _load("cot_chain", "m05_cot")


class CoTRAG:
    """
    CoT +two-pass RAG的完整实现

    三种运行模式 -对应论文的消融实验
    "rag_only" -> 只用 rag 不用 cot
    "cot_only" -> 只用 cot,不检索参考
    "rag_cot" -> RAG+COT 组合(论文里最优方案)
    """

    def __init__(self, retriever, top_k: int = TOP_K):
        self.retriever = retriever
        self.top_k = top_k

    def run(self,
            text: str,
            mode: str = "rag_cot",
            n_examples: int = 1,
            verbose: bool = False,
            ) -> dict:
        """对一段文字运行指定模式，返回完整过程记录"""
        if verbose:
            print(f"[cot_rag | {mode}] 原文{text}")

        # first pass
        if mode in ("rag_only", "rag_cot"):
            fp_refs = [r.text for r in self.retriever.retrieve(text, self.top_k)]
        else:
            fp_refs = []

        if mode == "rag_only":
            fp_mod = _load("first_pass", "m04_rag")
            fp_result = fp_mod.first_pass(text, self.retriever, self.top_k)

            fp_output = fp_result["output"]
            fp_chain = {}
        else:
            cot_mode = "cot"
            fp_result = _cot_chain.run_cot(
                text,
                mode=cot_mode,
                n_examples=n_examples,
                references=fp_refs if mode == "rag_cot" else None,
            )
            fp_output = fp_result["rewrite"]
            fp_chain = fp_result["parsed"]
        if verbose:
            print(f"  First Pass  → {fp_output}")

        # second pass
        if mode in ("rag_only", "rag_cot"):
            sp_refs = [r.text for r in self.retriever.retrieve(fp_output, self.top_k)]
        else:
            sp_refs = []

        if mode == "rag_only":
            sp_mod = _load("second_pass", "m04_rag")
            sp_result = sp_mod.second_pass(text, fp_output, self.retriever, self.top_k)
            sp_output = sp_result["output"]
            sp_chain = {}
        else:
            sp_result = _cot_chain.run_cot(
                fp_output,
                mode=cot_mode,
                n_examples=n_examples,
                references=sp_refs if mode == "rag_cot" else None,
            )
            sp_output = sp_result("rewrite")
            sp_chain = sp_result["parsed"]

        if verbose:
            print(f" second pass ->{sp_output}")

        return {
            "original": text,
            "mode": mode,
            "first_pass": {
                "output": fp_output,
                "refs": fp_refs,
                "chain": fp_chain,
            },
            "second_pass": {
                "output": sp_output,
                "refs": sp_refs,
                "chain": sp_chain,
            },
            "final_output": sp_output,
        }

    def run_batch(self, texts: list[str], **kwargs) -> list[dict]:
        return [self.run(t, **kwargs) for t in texts]

    def compare_modes(self, text: str, n_exmaples: int = 1) -> dict:
        """
        对同一段文字 同时跑三种模式，方便对比输出差异
        对应论文的消融实现(ablation study).
        """
        print(f"\n{'═' * 60}")
        print(f"  消融对比: {text}")
        print(f"{'═' * 60}")

        results = {}
        for mode in ("cot_only", "rag_only", "rag_cot"):
            r = self.run(text, mode=mode, n_examples=n_exmaples)
            results[mode] = r
            print(" [{mode:10s}]{r['final_output}")

            chain = r["first_pass"]["chain"]
            if chain.get("identified"):
                print(f"             识别: {chain['identified'][:2]}")
                print(f"             计划: {chain['plan'][:2]}")
        return results


def print_full_result(result: dict) -> None:
    """格式化打印单条完整结果。"""
    print(f"\n{'═' * 60}")
    print(f"  模式      : {result['mode']}")
    print(f"  原文      : {result['original']}")
    print(f"  最终输出  : {result['final_output']}")

    fp = result["first_pass"]
    sp = result["second_pass"]

    if fp["chain"].get("identified"):
        print(f"\n  ── First Pass CoT 推理 ──")
        print(f"  识别: {fp['chain']['identified']}")
        print(f"  计划: {fp['chain']['plan']}")
    if fp["refs"]:
        print(f"  检索参考: {fp['refs'][0][:60]}...")

    if sp["chain"].get("identified"):
        print(f"\n  ── Second Pass CoT 推理 ──")
        print(f"  识别: {sp['chain']['identified']}")
    if sp["refs"]:
        print(f"  检索参考: {sp['refs'][0][:60]}...")
    print(f"{'─' * 60}")


def test():
    retriever_mod = _load("retriever", "m03_embeddings")
    retriever = retriever_mod.Retriever()
    retriever.build_from_corpus(use_builtin=True)

    cot_rag = CoTRAG(retriever, top_k=3)

    # 单条完整测试
    test_inputs = [
        "The chairman must update his staff on the new company policy.",
        "Each policeman should submit his report before the end of his shift.",
        "The actress received her award at the ceremony last night.",
    ]

    print("\n" + "═" * 60)
    print("  CoT + RAG 完整流水线测试（rag_cot 模式）")
    print("═" * 60)
    for text in test_inputs:
        r = cot_rag.run(text, mode="rag_cot", verbose=True)
        print_full_result(r)

    # 消融对比
    print("\n\n" + "═" * 60)
    print("  消融对比：三种模式效果比较")
    print("═" * 60)
    cot_rag.compare_modes(
        "The fireman rescued the child and reported to his supervisor.",
    )


def main():
    test()


if __name__ == "__main__":
    main()
