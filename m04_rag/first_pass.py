#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: first_pass

输入：一段有性别偏见的文字（如 "The chairman must update his staff"）
做法：
1. 用这段文字去语料库里检索最相似的包容性参考(top-k)
2. 把参考内容+ 原文 + 指令拼成 prompt
3. 调用 llm 生成初步去偏版本

输出：初步去偏的文字(可能还不够自然，留给second pass 精练)

为什么First pass 还不够？
LLM 第一次见到这段文字，检索到的参考是基于"有偏见的原文"去找的。
召回的内容可能不够精准，第二次用去偏后的文字再检索，质量更好。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TOP_K, LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY

# 动态加载 m3_embeddings/retriever
import importlib.util

def _load(name: str, subdir: str):
    """
    动态加载带数字前缀目录里的模块。
    把目标 subdir 插到 sys.path 最前面，
    让被加载模块内部的 `from xxx import yyy` 也能找到同目录下的兄弟模块。
    """
    target_dir = Path(__file__).parent.parent / subdir
    target_dir_str = str(target_dir)
    if target_dir_str not in sys.path:
        sys.path.insert(0, target_dir_str)

    file_path = target_dir / f"{name}.py"
    if not file_path.exists():
        raise FileNotFoundError(
            f"找不到模块文件: {file_path}\n请检查目录名 '{subdir}' 是否正确"
        )

    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_first_pass_prompt(original: str, references: list[str]) -> str:
    """
    拼接 First pass 的 prompt
    结构 系统指令+包容性参考+ 原文 + 任务说明

    设计原则：
    明确告诉LLM任务目标，去除性别偏见，保持原意
    先给参考 让LLM知道好的写法是什么样的，
    再给原文 让LLM对照改写
    """
    refs_block = "\n".join(f" -{r} " for r in references)

    prompt = f""" 
    You are a writing assistant that rewrites text to use gender-inclusive language.
    INCLUSIVE LANGUAGE EXAMPLES (use these as reference for tone and style):
    {refs_block}
    
    ORIGINAL TEXT:
    {original}
    
    TASK:
    Rewrite the original text to:
    1. Replace gendered pronouns(he/she/his/her) with gender-neutral alternatives (they/their/them)
    2. Replace gendered job titles(chairman,fireman,etc.) with neutral equivalents(chairperson,firefighter, etc.)
    3. Preserve the original meaning,tone, and sentence structure as much as possible 
    4. Keep the rewrite natural and fluent
    
    provide ONLY the rewritten text,no explanation.
    """

    return prompt


def _call_llm(prompt: str) -> str:
    """
    调用 LLM 生成文本。
    有 API Key → 调用 OpenAI。
    没有 → 用本地规则替换模拟（用于离线调通管道）。
    """
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
            print(f"[first_pass] OpenAI 调用失败（{e}），降级到本地规则")

    # 复用 m1_data/gender_pairs 的替换逻辑
    gp = _load("gender_pairs", "m01_data")
    if "ORIGINAL TEXT:\n" in prompt:
        original = prompt.split("ORIGINAL TEXT:\n")[1].split("\n\nTASK:")[0].strip()
    else:
        original = prompt
    return gp.to_neutral(original)


def first_pass(
        original: str,
        retriever,
        top_k: int = TOP_K,
) -> dict:
    """
    first pass 主函数

    返回 dict 包含：
      original        原始有偏文字
      references      检索到的包容性参考
      prompt          发给 LLM 的 prompt（方便调试）
      output          LLM 输出的初步去偏版本
    """
    # step 1: 检索
    results = retriever.retrieve(original, top_k=top_k)
    references = [r.text for r in results]

    # step 2: 构建 prompt
    prompt = build_first_pass_prompt(original, references)

    # step 3: 调用 LLM
    output = _call_llm(prompt)

    return {
        "original": original,
        "references": references,
        "prompt": prompt,
        "output": output,
    }


def test():
    # 先加载检索器
    retriever_mod = _load("retriever", "m03_embeddings")
    retriever = retriever_mod.Retriever()
    retriever.build_from_corpus(use_builtin=True)

    test_inputs = [
        "The chairman must update his staff on the new company policy.",
        "Each policeman should submit his report before the end of his shift.",
        "The nurse said she would check on the patient after lunch.",
    ]

    print("=" * 60)
    print("  First Pass 测试")
    print("=" * 60)

    for text in test_inputs:
        result = first_pass(text, retriever, top_k=3)
        print(f"\n原文  : {result['original']}")
        print(f"参考  : {result['references'][0]}")
        print(f"输出  : {result['output']}")
        print(f"{'─' * 55}")


def main():
    test()


if __name__ == "__main__":
    main()
