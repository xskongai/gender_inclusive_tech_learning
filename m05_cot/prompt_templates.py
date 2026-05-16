#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/16/26
Description: prompt_templates

所有 prompt 模板
三种模式，复杂度递增
zero_shot
few_shot
cot
理解这三者的区别，是理解论文 COT 为什么有效的关键
"""
ZERO_SHOT_TEMPLATE = """Rewrite the following text using gender inclusive language.
Replace gendered pronouns and job titles with neutral alternatives.
Preserve the original meaning. 

Text:{text}
Rewritten: 
"""

FEW_SHOT_TEMPLATE = """Rewrite texts using gender-inclusive language. Here are examples:

Example 1:
Original: The fireman  rushed into the building to rescue the victim.
Rewritten: The firefighter rushed into the building to rescue the victim.

Example 2:
Original: Each employee must submit his report by Friday.
Rewritten: Each employee must submit their report by Friday.

Example 3:
Original:  The chairman called his secretary to reschedule the meeting.
Rewritten: The chairperson called their assistant to reschedule the meeting.
 
Now rewrite this text:
Original: {text}
Rewritten:

"""

COT_TEMPLATE = """You are an export in gender-inclusive language. Rewrite the given text step by step.

STEP 1 - IDENTIFY: list every word or phrase with gendered assumptions.
STEP 2 - PLAN: for each identified item, write the gender-neutral replacement.
STEP 3 - REWRITE: Apply all replacements and produce the final inclusive text.

{examples_block} Text: {text}

Work through each step:
STEP 1 - IDENTIFY:"""

COT_EXAMPLES = [
    {
        "text": "The policeman filed his report after the incident. ",
        "step1": "- 'policeman' -> gendered job title\n- 'his' -> gendered pronoun ",
        "step2": "- 'policeman' -> 'police officer'\n 'his' ->'their' ",
        "rewrite": "The police officer filed their report after the incident. "
    },
    {
        "text": "Every businessman should review his contracts carefully.  ",
        "step1": "- 'businessman' -> gendered job title\n - 'his' -> gendered pronoun ",
        "step2": "- 'businessman' -> 'businessperson'\n - 'his' -> 'their' ",
        "rewrite": "Every businessperson should review their contracts carefully. "
    }
]


def build_cot_examples_block(n: int = 1) -> str:
    """
    把 CoT 示例 格式化成 prompt里的 examples_block.
    n 控制用几个示例(0 = 零样本 Cot, 1-2 = 少样本 cot).
    """

    if n == 0:
        return ""

    block = "EXAMPLES:\n"
    for ex in COT_EXAMPLES[:n]:
        block = f"""
        Text: {ex['text']}
        STEP 1 - IDENTIFY:
        {ex['step1']}
        STEP 2 - PLAN:
        {ex['step2']}
        STEP 3 - REWRITE:
        {ex['rewrite']}
        ---
        """
    return block + "\n"


def build_zero_shot_prompt(text: str) -> str:
    return ZERO_SHOT_TEMPLATE.format(text=text)


def build_few_shot_prompt(text: str) -> str:
    return FEW_SHOT_TEMPLATE.format(text=text)


def build_cot_prompt(text: str, n_examples: int = 1) -> str:
    """
    构造 CoT prompt.
    n_examples = 0 -> 0样本Cot LLM 自己想推理格式
    n_examples = 1 -> 1样本 Cot 给一个完整推理示例

    n_examples = 2 二本样 Cot  更稳定，但是 token 更多。
    """
    examples_block = build_cot_examples_block(n_examples)
    return COT_TEMPLATE.format(
        examples_block=examples_block,
        text=text,
    )


def build_rag_cot_prompt(
        text: str,
        references: list[str],
        n_examples: int = 1,
) -> str:
    """
    RAG+CoT 组合 prompt (m04_rag +m05_cot)的组合
    在cot 步骤之前先给出检索到的包容性参考。
    让LLM 即有推理框架，又有具体的语言参考。
    """
    refs_block = "\n".join(f"  - {r}" for r in references)
    examples_block = build_cot_examples_block(n_examples)

    return f"""You are an export in gender-inclusive language.
    INCLUSIVE LANGUAGE REFERENCES(use for style and vocabulary guidance):
    {refs_block}
    
    {examples_block} Now rewrite the following text step by step.
    
    Text:{text}
    
    STEP 1 - INDENFIFY:
    """


def test():
    sample = "The chairman must update his staff on the new policy. "

    print("----[zero-shot prompt]----")
    print(build_zero_shot_prompt(sample))

    print("----[few-shot prompt]----")
    print(build_few_shot_prompt(sample))

    print("----[cot prompt(1-shot)]----")
    print(build_cot_prompt(sample, n_examples=1))

    print("----[RAG + CoT prompt]----")
    refs = [
        "The manager updated their team on the new guidelines. ",
        "Every employee should be informed about policy changes. ",
    ]
    print(build_rag_cot_prompt(sample, refs, n_examples=1))


def main():
    test()


if __name__ == "__main__":
    main()
