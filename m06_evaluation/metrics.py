#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/16/26
Description: metrics

不依赖LLM，用词表和正则直接计算，速度快，完全可复现。

三个指标：
bias_word_count 原文 / 改写中 检测到的偏见词数量
neutrality_rate 偏见词被替换的比例 越高越好
meaning_preserved 简单检测原意保留 (共同词汇比例)
"""

import re
import sys
from pathlib import Path

from m02_corpus.inspector import BIASED_WORDS

sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util


def _load(name: str, subdir: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / subdir / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gp = _load("gender_pairs", "m01_data")

BIASED_WORDS = set(_gp.GENDER_TO_NEUTRAL.keys()) | {
    "he", "she", "his", "her", "him",
    "himself", "herself", "actress", "stewardess",
    "congressman", "congresswoman",
}


def _tokenize(text: str) -> list[str]:
    """提取所有小写词，去掉标点。"""
    return re.findall(r"\b[a-z]+\b", text.lower())


def count_biased_words(text: str) -> dict:
    """统计文本中检测到的偏见词"""
    tokens = _tokenize(text)
    found = [t for t in tokens if t in BIASED_WORDS]
    return {
        "count": len(found),
        "words": found,
    }


def neutrality_rate(original: str, rewrite: str) -> float:
    """改写消除偏见词的比例 = 1 -改写中剩余词数/原文偏见词数"""
    orig_count = count_biased_words(original)["count"]
    if orig_count == 0:
        return 1.0
    rewrite_count = count_biased_words(rewrite)["count"]
    # 用 max(0,...) 防止改写引入了新偏见词导致负数
    return max(0.0, round(1.0 - rewrite_count / orig_count, 4))


def content_overlap(original: str, rewrite: str) -> float:
    """
   内容词重叠率：衡量改写是否保留了原意。
   计算方法：去掉偏见词后，两边剩余词汇的 jaccard相似度。
    """
    orig_words = set(_tokenize(original)) - BIASED_WORDS
    rewrite_words = set(_tokenize(rewrite)) - BIASED_WORDS

    if not orig_words:
        return 1.0

    intersection = orig_words & rewrite_words
    union = orig_words | rewrite_words

    return round(len(intersection) / len(union), 4)


def score_pair(original: str, rewrite: str) -> dict:
    """
    对一对（原文，改写）计算所有规则指标，返回汇总dict
    """
    orig_bias = count_biased_words(original)
    rewrite_bias = count_biased_words(rewrite)
    n_rate = neutrality_rate(original, rewrite)
    overlap = content_overlap(original, rewrite)

    # 综合规则分 中立率 60% 内容保留占 40%
    rule_score = round(n_rate * 0.6 + overlap * 0.4, 4)

    return {
        "original_bias_count": orig_bias["count"],
        "original_bias_words": orig_bias["words"],
        "rewrite_bias_count": rewrite_bias["count"],
        "rewrite_bias_words": rewrite_bias["words"],
        "neutrality_rate": n_rate,
        "content_overlap": overlap,
        "rule_score": rule_score,  # 0-1 越高越好
    }


def score_batch(pairs: list[dict]) -> list[dict]:
    """
    批量评分 pairs:[{"original":...,"rewrite":...},...]
    """
    results = []
    for p in pairs:
        scores = score_pair(p["original"], p["rewrite"])
        results.append({**p, **scores})
    return results


def test():
    test_pairs = [
        {
            "original": "The chairman must update his staff on the new policy.",
            "rewrite": "The chairperson must update their staff on the new policy.",
        },
        {
            "original": "Each policeman should submit his report before his shift ends.",
            "rewrite": "Each police officer should submit their report before their shift ends.",
        },
        {
            "original": "The nurse said she would check on the patient.",
            "rewrite": "The nurse said they would check on the patient.",
        },
        {
            "original": "The doctor reviewed his patient notes carefully.",
            "rewrite": "The doctor reviewed his patient notes carefully.",  # 未改写，测试检测
        },
    ]

    print("=" * 60)
    print("  规则评估结果")
    print("=" * 60)
    for p in score_batch(test_pairs):
        print(f"\n  原文  : {p['original']}")
        print(f"  改写  : {p['rewrite']}")
        print(f"  原文偏见词 : {p['original_bias_words']}")
        print(f"  残留偏见词 : {p['rewrite_bias_words']}")
        print(f"  中立率    : {p['neutrality_rate']:.2%}")
        print(f"  内容重叠  : {p['content_overlap']:.2%}")
        print(f"  综合分    : {p['rule_score']:.4f}")
        print("─" * 55)


def main():
    test()


if __name__ == "__main__":
    main()
