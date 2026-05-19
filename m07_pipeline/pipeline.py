#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/19/26
Description: pipeline 端到端流水线
把所有模块串联成为一个统一的 pipeline类
调用方只需要
p = pipeline()
p.setup()
results = p.run(texts,modes =["cot_only","rag_only","rag_cot"])

内部自动完成：
语料构建 -> 嵌入建索引 -> CotRag 改写 -> 评估打分
"""
import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _load(name: str, subdir: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / subdir / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Pipeline:
    """
    端到端实验流水线
    组件：
    retriever <- m03_embeddings.Retriever
    cot_rag <- m05_cot.CoTRAG
    evaluator <- m06_evaluation.Evaluator
    """

    def __init__(self):
        self.retriever = None
        self.cot_rag = None
        self.evaluator = None
        self._ready = False

    def setup(self, force_rebuild: bool = False) -> None:
        """
        初始化所有组件
        force_rebuild:false,已有索引直接复用，不重新嵌入
        """
        print("\n" + "═" * 55)
        print("  Pipeline 初始化")
        print("═" * 55)

        # m03 检索器
        retriever_mod = _load("retriever", "m03_embedddins")
        self.retriever = retriever_mod.Retriever()
        self.retriever.build_from_corpus(
            use_builtin=True,
            force_rebuild=force_rebuild,
        )

        # m05 CoTRAG(内含 m4_rag的 Two-pass)
        cot_rag_mod = _load("cot_rag", "m5_cot")
        self.cot_rag = cot_rag_mod.CoTRAG(self.retriever, top_k=5)

        evaluator_mod = _load("evaluator", "m06_evaluation")
        self.evaluator = evaluator_mod.Evaluator()

        self._ready = True

        print("所有组件就绪")

    def run(
            self,
            texts: list[str],
            modes: list[str] | None = None,
            n_examples: int = 1,
            use_llm_eval: bool = True,
    ) -> dict:
        """
        对 texts 中每条文字，用modes 中每种模式改写，然后评估
        返回
        outputs: 改写结果 按mode 分组
        records: 所有评估记录
        summary: 每种mode 的平均分
        """
        if not self._ready:
            raise RuntimeError("please invoke setup first")
        modes = modes or ["cot_only", "rag_only", "rag_cot"]

        # step 1:rewrite
        print("step 1:rewrite")
        all_outputs = []
        for mode in modes:
            print(f"mode:{mode} ({len(texts)})")

            for text in texts:
                result = self.cot_rag.run(
                    text,
                    mode=mode,
                    n_examples=n_examples,
                )
                all_outputs.append({
                    "original": text,
                    "final_output": result["final_output"],
                    "mode": mode,
                    "detail": result,
                })

        # step 2:eval
        print("step 2:eval")

        records = self.evaluator.evaluate(
            all_outputs,
            use_llm=use_llm_eval,
        )

        # step 3:summary
        print("step 3:summary")

        summary = self._summarize(records)
        return {
            "outputs": all_outputs,
            "records": records,
            "summary": summary,
        }

    def _summarize(self,
                   records) -> dict:
        """
        按 mode 计算各指标平均值。
        """
        from collections import defaultdict
        groups = defaultdict(list)

        for r in records:


        print()


def main():
    pass


if __name__ == "__main__":
    main()
