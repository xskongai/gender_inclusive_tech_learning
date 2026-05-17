#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/16/26
Description: llm_judge

让LLM扮演评委，对改写结果打分。
对应论文的三个评估维度
gender_assumption 原文的性别假设程度 1 无假设 5 严重假设
gender_neutrality 改写的中立程度  1，仍有偏见   5 完全中立
quality_relevance 改写的质量与相关性 1 差， 5优秀

为什么用 LLM 而不只用规则？
规则 只能检测词表里的词，漏掉语义层面的偏见
比如 The engineer showed his team  his 在词表里
但 the engineer demonstrated confidence in the meeting.
这种隐性假设规则 就检测不到

输出格式设计： 要求llm 输出 JSON，方便解析和汇总
"""

import re
import json
import sys
from pathlib import Path

from click import prompt
from sympy.series.gruntz import rewrite

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator of gender-inclusive language.
Evaluate the rewriting quality on three dimensions.
RESPOND ONLY with valid JSON.

ORIGINAL:{original}
REWRITTEN:{rewrite}

Score each dimension from 1 to 5:

gender_assumption (score for the ORIGINAL text):
    1 = no gendered assumptions
    3 = some gendered assumptions
    5 = strong gendered assumptions

gender_neutrality(score for the REWRITTEN text):
    1 = still contains gendered language
    3 = partially neutralized
    5 = fully gender-neutral 

quality_relevance (score for the REWRITTEN text):
    1 = meaning lost or awkward phrasing
    3 = meaning preserved but slightly unnatural
    
    
"""


def _call_llm(prompt: str) -> str:
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[llm_judge] OpenAI 失败（{e}），降级本地评估")

    return _local_judge(prompt)


def _local_judge(prompt: str) -> str:
    """
    离线模式：用规则估算三个分数，构造json格式返回
    规则逻辑：
    gender_assumption -> 数原文偏见词数量
    gender_neutrality -> 改写后偏见词数量 反向
    quality_relevance -> 词汇重叠率
    """
    import importlib.util
    def _load(name, subdir):
        spec = importlib.util.spec_from_file_location(
            name, Path(__file__).parent.parent / subdir / f"{name}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        return mod

    metrics = _load("metrics", "m06_evaluation")

    orig = re.search(r"ORIGINAL: (.+)", prompt)
    rewrite = re.search(r"REWRITTEN: (.+)", prompt)

    if not orig or not rewrite:
        return '{"gender_assumption":3,"gender_neutrality":3,"quality_relevance":3,"reasoning":"parse error"}'

    orig_text = orig.group(1).strip()
    rewrite_text = rewrite.group(1).strip()
    scores = metrics.score_pair(orig_text, rewrite_text)

    def to_5(val: float) -> int:
        return max(1, min(5, round(val * 4 + 1)))

    bias_count = scores["original_bias_count"]
    g_assumption = min(5, max(1, bias_count * 2))
    g_neutrality = to_5(scores["neutrality_rate"])
    q_relevance = to_5(scores["content_overlap"])

    return json.dumps({
        "gender_assumption": g_assumption,
        "gender_neutrality": g_neutrality,
        "quality_relevance": q_relevance,
        "reasoning": f"Rule_based:{bias_count} biased words in original, "
                     f"neutrality_rate = {scores['neutrality_rate']:.2f}, "
                     f"overlap = {scores['content_overlap']:.2f}",
    })


def _parse_scores(raw: str) -> dict:
    """
    从 LLM 输出中提取 JSON。
    LLM 有时会在 JSON 前后加解释文字，需要先找到 JSON 块。
    """
    # 先尝试直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 找第一个 { ... } 块
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 兜底：用正则提取数字
    result = {"reasoning": "parse failed"}
    for key in ("gender_assumption", "gender_neutrality", "quality_relevance"):
        m = re.search(rf'"{key}"\s*:\s*(\d)', raw)
        result[key] = int(m.group(1)) if m else 3
    return result


def judge(original: str, rewrite: str) -> dict:
    """
    对一对 原文，改写 打分
    返回包含三个维度分数和推理的dict
    """
    prompt = JUDGE_PROMPT_TEMPLATE.format(original=original, rewrite=rewrite)
    raw = _call_llm(prompt)
    scores = _parse_scores(raw)

    for key in ("gender_assumption", "gender_neutrality", "quality_relevance"):
        scores[key] = max(1, min(5, int(scores.get(key, 3))))

    # 综合分：中立性和质量各占一半（不含 assumption，那是描述原文的）
    scores["llm_score"] = round(
        (scores["gender_neutrality"] + scores["quality_relevance"]) / 2, 2)
    scores["raw_response"] = raw
    return scores


def judge_batch(pairs: list[dict]) -> list[dict]:
    """ 批量评分，pairs:[{"original":..., "rewrite":...}, ...]"""
    results = []
    for i, p in enumerate(pairs):
        print(f" [llm_judge]评分{i + 1}/{len(pairs)}...")
        scores = judge(p["original"], p["rewrite"])
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
            "original": "The doctor reviewed his patient notes carefully.",
            "rewrite": "The doctor reviewed his patient notes carefully.",  # 未改，测试检测
        },
    ]
    print("=" * 60)
    print("  LLM-as-a-Judge 评估结果")
    print("=" * 60)

    for r in judge_batch(test_pairs):
        print(f"\n  原文  : {r['original']}")
        print(f"  改写  : {r['rewrite']}")
        print(f"  性别假设（原文）: {r['gender_assumption']}/5")
        print(f"  中立性（改写）  : {r['gender_neutrality']}/5")
        print(f"  质量相关性      : {r['quality_relevance']}/5")
        print(f"  综合 LLM 分     : {r['llm_score']}/5")
        print(f"  推理  : {r.get('reasoning', '')}")
        print("─" * 55)


def main():
    test()


if __name__ == "__main__":
    main()
