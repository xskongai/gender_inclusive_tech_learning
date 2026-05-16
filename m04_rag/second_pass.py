#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: second_pass
RAG 第二次检索+ 精练
输入 first pass 的 输出(已初步去偏 ，但可能还不够自然)
做法
1. 用 first pass 的输出再检索一次语料库
此时查询已经是中性语言，检索结果会更精练
2.拼新的 prompt,重点从去偏 转向 语言精练
3. LLM 在更好的参考下输出最终版本

和 first pass 核心区别
- 查询文本不同：first pass 用原文查，second pass 用去偏后的文字查
- prompt 重点不同： first pass 强调替换偏见词 second pass 强调让语言更流畅
- 参考质量更高：去偏后的文字和包容性语料语义更接近，如回更精准
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TOP_K, OPENAI_API_KEY

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


def build_second_pass_prompt(
        original: str,
        first_pass_output: str,
        references: list[str],
) -> str:
    """
    second pass 的 prompt 比 first pass 多个一个维度
    同时给llm 看原文，第一次输出 ，和新的参考
    让他知道 ，从哪来，到了哪，还差什么
    """
    refs_block = "\n".join(f" -{r}" for r in references)

    prompt = f"""
    You are a writing assistant specializing in gender-inclusive language. 
    
    INCLUSIVE LANGUAGE EXAMPLES(reference for fluency and style):
    {refs_block}
    
    ORIGINAL TEXT (may contain gendered language):
    {original}
    
    FIRST DRAFT(gender-neutral but may need refinement):
    {first_pass_output}
    
    TASK:
    Review the first draft and produce a final, polished version that:
    1. Ensures all gendered language has been replaced (check for any missed pronouns or titles)
    2. Reads naturally and fluently - fix any awkward phrasing from the first draft
    3. Preserves the original meaning faithfully
    4. Matches the tone and register of the original 
    
    Provide ONLY the final rewritten text, no explanation 
    """
    return prompt


def _call_llm(prompt: str) -> str:
    import os
    print(f"[debug] config.OPENAI_API_KEY = {repr(OPENAI_API_KEY)[:30]}")
    print(f"[debug] os.environ.OPENAI_API_KEY = {repr(os.environ.get('OPENAI_API_KEY'))[:30]}")
    print(f"[debug] bool(OPENAI_API_KEY) = {bool(OPENAI_API_KEY)}")
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            from config import LLM_MODEL, LLM_TEMPERATURE
            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                temperature=LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[second_pass] OpenAI 调用失败（{e}），降级到本地规则")

    # 离线模式：对 first_pass 的输出再做一次规则清洗
    gp = _load("gender_pairs", "m01_data")
    if "FIRST DRAFT" in prompt:
        draft = prompt.split("FIRST DRAFT (gender-neutral but may need refinement):\n")[1]
        draft = draft.split("\n\nTASK:")[0].strip()
    else:
        draft = prompt
    return gp.to_neutral(draft)


def second_pass(
        original: str,
        first_pass_output: str,
        retriever,
        top_k: int = TOP_K
) -> dict:
    """
    Second Pass 主函数。

    返回 dict 包含：
      original            原始文字
      first_pass_output   第一次输出
      references          第二次检索到的参考（基于 first_pass_output 查询）
      prompt              发给 LLM 的 prompt
      output              最终精炼版本
    """
    # step 1: 用 first_pass 的输出重新检索(核心差异所在)
    results = retriever.retrieve(first_pass_output, top_k=top_k)
    references = [r.text for r in results]

    # step 2: 构建 prompt
    prompt = build_second_pass_prompt(original, first_pass_output, references)

    # step 3: 高用 llm
    output = _call_llm(prompt)

    # step 3: 调用LLM
    return {
        "original": original,
        "first_pass_output": first_pass_output,
        "references": references,
        "prompt": prompt,
        "output": output,
    }


def test():
    retriever_mod = _load("retriever", "m03_embeddings")
    retriever = retriever_mod.Retriever()
    retriever.build_from_corpus(use_builtin=True)

    test_cases = [
        {
            "original": "The chairman must update his staff on the new policy.",
            "first_pass_output": "The chairperson must update their staff on the new policy.",
        },
        {
            "original": "Each policeman should submit his report before the end of his shift.",
            "first_pass_output": "Each police officer should submit their report before the end of their shift.",
        },
    ]

    print("=" * 60)
    print("  Second Pass 测试")
    print("=" * 60)

    for case in test_cases:
        result = second_pass(
            original=case["original"],
            first_pass_output=case['first_pass_output'],
            retriever=retriever,
            top_k=3,
        )

        print(f"\n原文      : {result['original']}")
        print(f"First Pass: {result['first_pass_output']}")
        print(f"参考      : {result['references'][0]}")
        print(f"最终输出  : {result['output']}")
        print("─" * 55)


def main():
    test()


if __name__ == "__main__":
    main()
