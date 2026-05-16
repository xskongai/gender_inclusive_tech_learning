#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/16/26
Description: cot_chain
把 prompt_templates + LLM 调用串起来，同时解析 LLM输出推理步骤

LLM 按 COT 格式输出时，回复长这样
step 1 - identify:
- 'chairman' -> gendered job title
- 'his'  -> gendered pronoun
step 2 - PLAN:
- 'chairman' -> 'chairperson'
- 'his' -> 'their'
step 3 - rewrite:
- the chairperson must update their staff on the new policy

我们需要把三个部分分别提取出来，方便后续分析和评估
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

import importlib.util


def _load(name: str, subdir: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / subdir / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_templates = _load("prompt_templates", "m05_cot")


# ─────────────────────────────────────────────────────
# LLM 调用（和 m4_rag 相同的双模式策略）
# ─────────────────────────────────────────────────────
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
            print(f"[cot_chain] OpenAI 失败（{e}），降级本地")

    # 离线模式：生成模拟的 CoT 推理输出
    return _local_cot_simulate(prompt)


def _local_cot_simulate(prompt: str) -> str:
    """
    离线模式下模拟CoT输出
    用 m1_data/gender_pairs 的规则找出偏见词
    构造符合Cot格式的LLM 输出,让整个链路可以跑通。
    """
    gp = _load("gender_pairs", "m01_data")

    # 从 prompt 里提取原文
    if "Text: " in prompt:
        lines = prompt.split("Text: ")
        text = lines[-1].split("\n")[0].strip()
    else:
        text = prompt

    # 找偏见词
    words = text.split()
    biased = []
    for w in words:
        clean_w = w.lower().strip(".,!?;:")
        if clean_w in gp.GENDER_TO_NEUTRAL:
            biased.append((w, gp.GENDER_TO_NEUTRAL[clean_w]))

    # 构造 CoT 格式输出
    if biased:
        step1 = "\n".join(f"- '{w}' → gendered term" for w, _ in biased)
        step2 = "\n".join(f"- '{w}' → '{rep}'" for w, rep in biased)
    else:
        step1 = "- No obvious gendered terms found"
        step2 = "- No replacements needed"

    rewrite = gp.to_neutral(text)

    return (
        f"{step1}\n"
        f"STEP 2 - PLAN:\n{step2}\n"
        f"STEP 3 - REWRITE:\n{rewrite}"
    )


def parse_cot_output(raw_output: str) -> dict:
    """
    将LLM 的 Cot 格式 输出拆成三个部分。
    输入 (raw_output 是 step1 之后的全部内容，因为 prompt里已经写了 IDENTITY:)
    -'chairman' -> gendered job title
    step 2 -Plan
    - 'chairman' -> 'chairperson'
    step 3 -rewrite:
    the chairperson must update their staff.

    返回：
    {
    "identified": ["'chairman' -> gendered job title",...],
    "plan":["'chairman' -> 'chairperson'",...]
    "rewrite": "The chairperson must update their staff.",
    "raw": 完整原始输出
    }
    """
    result = {"identified": [], "plan": [], "rewrite": "", "raw": raw_output}

    # 按 STEP 标记分割
    step2_match = re.search(r"STEP\s*2\s*[-–]\s*PLAN\s*:?", raw_output, re.IGNORECASE)
    step3_match = re.search(r"STEP\s*3\s*[-–]\s*REWRITE\s*:?", raw_output, re.IGNORECASE)

    if step2_match and step3_match:
        step1_text = raw_output[: step2_match.start()].strip()
        step2_text = raw_output[step2_match.end(): step3_match.start()].strip()
        step3_text = raw_output[step3_match.end():].strip()
    elif step3_match:
        step1_text = raw_output[:step2_match.start()].strip()
        step2_text = ""
        step3_text = raw_output[step3_match.end():].strip()
    else:
        result["rewrite"] = raw_output.strip()
        return result

    # 提取列表项（以 - 或 • 开头的行）
    def extract_bullets(text: str) -> list[str]:
        lines = [l.strip().lstrip("-•·").strip() for l in text.splitlines()]
        return [l for l in lines if l]

    result["identified"] = extract_bullets(step1_text)
    result["plan"] = extract_bullets(step2_text)
    result["rewrite"] = step3_text.strip()

    return result


def run_cot(
        text: str,
        mode: str = "cot",
        n_examples: int = 1,
        references: list[str] | None = None,
) -> dict:
    """
    对一段文字 运行指定模式的 COT 链

    返回：
    {
    "original": 原文
    “mode":  使用的模式
    "prompt": 发给LLM的完整 prompt
    "raw_output": LLM的原始输出
    "parsed": 解析后的 COT 三步结构
    "rewrite": 最终改写结果（快速访问）
    }
    """
    if mode == "zero_shot":
        prompt = _templates.build_zero_shot_prompt(text)
    elif mode == "few_shot":
        prompt = _templates.build_few_shot_prompt(text)
    elif mode == "cot" and references:
        prompt = _templates.build_rag_cot_prompt(text, references, n_examples)
    else:
        prompt = _templates.build_cot_prompt(text, n_examples)
    # 调用 LLM
    raw_output = _call_llm(prompt)

    # 解析输出
    if mode in ("cot",) or (mode == "cot" and references):
        parsed = {"rewrite": raw_output.strip(), "raw": raw_output}
    else:
        parsed = {"rewrite": raw_output.strip(), "raw": raw_output}

    return {
        "original": text,
        "mode": mode,
        "prompt": prompt,
        "raw_output": raw_output,
        "parsed": parsed,
        "rewrite": parsed.get("rewrite", raw_output.strip()),
    }


def test():
    samples = [
        "The chairman must update his staff on the new company policy.",
        "Each policeman should submit his report before the end of his shift.",
        "The actress received her award at the ceremony last night.",
    ]

    for mode in ["zero_shot", "few_shot", "cot"]:
        print(f"\n{'═' * 60}")
        print(f"  模式: {mode}")
        print(f"{'═' * 60}")

        for text in samples[:2]:
            result = run_cot(text, mode=mode)
            print(f"\n  原文   : {result['original']}")
            if mode == "cot" and result["parsed"].get("identified"):
                print(f"  识别   : {result['parsed']['identified']}")
                print(f"  计划   : {result['parsed']['plan']}")
            print(f"  改写   : {result['rewrite']}")


def main():
    test()


if __name__ == "__main__":
    main()
