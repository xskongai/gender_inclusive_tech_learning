#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/16/26
Description: evaluator 综合评估器，对外入口
把规则评估 metrics 和  LLM 评估 对一批 pipeline 输出结果生成完整报告
对应的论文实验表格 每种模式（rag_only/cot_only/rag_cot)
"""
import json
import sys
from pathlib import Path
from dataclasses import dataclass, asdict

from m06_evaluation.metrics import neutrality_rate

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_PROCESSED

import importlib.util


def _load(name: str, subdir: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / subdir / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_metrics = _load("metrics", "m06_evaluation")
_llm_judge = _load("llm_judge", "m06_evaluation")


@dataclass
class EvalRecord:
    """ 单条评估记录，包括 原文，改写，两套分数。"""
    original: str
    rewrite: str
    mode: str

    # rule score 规则分
    neutrality_rate: float
    content_overlap: float
    rule_score: float

    # LLM score
    gender_assumption: int
    gender_neutrality: int
    quality_relevance: int
    llm_score: float

    final_score: float  # 规则分*0.4+LLM分/5 *0.6


class Evaluator:
    """
    综合评估器

    用法 ev = Evaluator()
    records = ev.evaluate(pipeline_outputs)
    ev.print_report(records)
    ev.save_report(records,"results.json")
    """

    def evaluate(
            self,
            pipeline_outputs: list[dict],
            use_llm: bool = True,
    ) -> list[EvalRecord]:
        """
        对 pipeline 输出批量评估
        pipeline_outputs 的每条 dict需要包含：
        "original" 原文
        "final_output" 最终改定（来自m4_rag 或 m5_cot的 run()输出
        "mode" 模式名 可选
        """
        records = []
        total = len(pipeline_outputs)

        for i, item in enumerate(pipeline_outputs, 1):
            original = item.get("original", "")
            rewrite = item.get("final_output", item.get("rewrite", ""))
            mode = item.get("mode", "unknown")

            print(f"[evaluator]评估{i}/{total}:{original[:40]}...")

            rule = _metrics.score_pair(original, rewrite)

            if use_llm:
                llm = _llm_judge.judge(original, rewrite)
            else:
                llm = {
                    "gender_assumption": 3,
                    "gender_neutrality": 3,
                    "quality_relevance": 3,
                    "llm_score": 3.0,
                }

            llm_score_norm = llm["llm_score"] / 5.0  # 归一化到 0-1
            final_score = round(rule["rule_score"] * 0.4 + llm_score_norm * 0.6, 4)

            records.append(
                EvalRecord(
                    original=original,
                    rewrite=rewrite,
                    mode=mode,
                    neutrality_rate=rule["neutrality_rate"],
                    content_overlap=rule["content_overlap"],
                    rule_score=rule["rule_score"],
                    gender_assumption=llm["gender_assumption"],
                    gender_neutrality=llm["gender_neutrality"],
                    quality_relevance=llm["quality_relevance"],
                    llm_score=llm["llm_score"],
                    final_score=final_score,
                )
            )

            return records

    def print_report(self, records: list[EvalRecord]) -> None:
        """格式化打印评估报告，含逐条详情和汇总统计。"""
        if not records:
            print("[evaluator] 无数据")
            return

        print("\n" + "═" * 65)
        print("  评估报告")
        print("═" * 65)

        # 按 mode 分组汇总
        mode_groups: dict[str, list[EvalRecord]] = {}
        for r in records:
            mode_groups.setdefault(r.mode, []).append(r)

        # 逐条打印
        for r in records:
            print(f"\n  原文  : {r.original}")
            print(f"  改写  : {r.rewrite}")
            print(f"  模式  : {r.mode}")
            print(f"  规则分 → 中立率:{r.neutrality_rate:.0%}  "
                  f"内容重叠:{r.content_overlap:.0%}  "
                  f"rule_score:{r.rule_score:.3f}")
            print(f"  LLM分  → 假设:{r.gender_assumption}/5  "
                  f"中立:{r.gender_neutrality}/5  "
                  f"质量:{r.quality_relevance}/5  "
                  f"llm_score:{r.llm_score:.2f}")
            print(f"  综合分 → {r.final_score:.4f}")
            print("─" * 60)

        # 各模式汇总
        print("\n" + "═" * 65)
        print("  各模式平均分")

    def save_report(
            self,
            records: list[EvalRecord],
            filename: str = "eval_report.json",
    ) -> Path:
        """把评估结果序列化存盘，供后续分析。"""
        out_path = DATA_PROCESSED / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)
        print(f"[evaluator] 报告已保存 → {out_path}")
        return out_path


def test():
    # 模拟三种模式的 pipeline 输出
    mock_outputs = mock_outputs = [
        {
            "original": "The chairman must update his staff on the new policy.",
            "final_output": "The chairperson must update their staff on the new policy.",
            "mode": "rag_cot",
        },
        {
            "original": "Each policeman should submit his report before his shift.",
            "final_output": "Each police officer should submit their report before their shift.",
            "mode": "rag_cot",
        },
        {
            "original": "The chairman must update his staff on the new policy.",
            "final_output": "The chairperson must update their staff on the new policy.",
            "mode": "cot_only",
        },
        {
            "original": "Each policeman should submit his report before his shift.",
            "final_output": "Each police officer should submit their report before their shift.",
            "mode": "cot_only",
        },
        {
            "original": "The chairman must update his staff on the new policy.",
            "final_output": "The chairman must update his staff on the new policy.",  # 未改
            "mode": "baseline",
        },
    ]
    ev = Evaluator()
    records = ev.evaluate(mock_outputs, use_llm=True)
    ev.print_report(records)
    ev.save_report(records, "eval_report.json")


def main():
    test()


if __name__ == "__main__":
    main()
