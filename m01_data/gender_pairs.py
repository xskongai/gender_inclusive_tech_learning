#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/12/26
Description: gender_pairs
性别词 ->中性词替换
职责：
1. 维护一张性别词 ->中性词的映射表(对应论文 的 gender neutral pairs )
2. 实现文本替换函数
3. 支持反事实句对生成 (把 he, 换成 she, 或换成 type )

这是论文 "数据处理层"的核心：构造 无偏语料和反事实对都依赖这里。
"""
import re

# ── 性别词 → 中性词映射表 ─────────────────────────────
# 格式：{有性别词: 中性替代词}
# 来源：论文 Gender Neutral Pairs.xlsx 的代表性子集
GENDER_TO_NEUTRAL: dict[str, str] = {
    # 职业名词
    "chairman": "chairperson",
    "chairwoman": "chairperson",
    "fireman": "firefighter",
    "firewoman": "firefighter",
    "policeman": "police officer",
    "policewoman": "police officer",
    "stewardess": "flight attendant",
    "steward": "flight attendant",
    "mankind": "humankind",
    "manpower": "workforce",
    "businessman": "businessperson",
    "businesswoman": "businessperson",
    "congressman": "legislator",
    "congresswoman": "legislator",
    "spokesman": "spokesperson",
    "spokeswoman": "spokesperson",
    "mailman": "mail carrier",
    "waiter": "server",
    "waitress": "server",
    "actor": "performer",
    "actress": "performer",
    "he/she": "they",
    "his/her": "their",
    "him/her": "them",
    # 代词
    "he": "they",
    "she": "they",
    "his": "their",
    "her": "their",
    "him": "them",
}

# 反事实替换  he ->she
MAIL_TO_FEMALE: dict[str, str] = {
    "he": "she", "him": "her", "his": "her",
    "himself": "herself", "man": "woman", "men": "women",
    "boy": "girl", "boys": "girls", "male": "female",
    "mr": "ms", "son": "daughter", "father": "mother",
    "brother": "sister", "husband": "wife", "uncle": "aunt",
    "nephew": "niece", "king": "queen", "prince": "princess",
}
FEMALE_TO_MALE: dict[str, str] = {v: k for k, v in MAIL_TO_FEMALE.items()}


def _replace_words(text: str, mapping: dict[str, str]) -> str:
    """
    大小写不敏感的全词替换。
    "whole word" 保证 "he" 不会替换 "the" 里的 he。
    替换后保持原来的大小写形式（首字母大写 → 结果首字母也大写）。
    """

    def replacer(match: re.Match) -> str:
        word = match.group(0)
        replacement = mapping[word.lower()]
        if word[0].isupper():
            return replacement.capitalize()
        return replacement

    pattern = r"\b(" + "|".join(re.escape(w) for w in mapping) + r")\b"
    return re.sub(pattern, replacer, text, flags=re.IGNORECASE)


def to_neutral(text: str) -> str:
    """把文本中的性别词替换成为中性词。"""
    return _replace_words(text, GENDER_TO_NEUTRAL)


def male_to_female(text: str) -> str:
    """反事实：把男性词替换同成女性词 用于构造反事实句对"""
    return _replace_words(text, MAIL_TO_FEMALE)


def female_to_male(text: str) -> str:
    """反事实：把女性替换为男性词"""
    return _replace_words(text, FEMALE_TO_MALE)


def make_counterfactual_pair(text: str) -> dict:
    """
    给定一个句子，生成事实三元组：
    original/male_version/female_version/neural_version
    对应的论文的 counterfactural sentence tuples
    """
    return {
        "original": text,
        "male_version": female_to_male(text),
        "female_version": male_to_female(text),
        "neutral_version": to_neutral(text),
    }


def test():
    test_sentences = [
        "The chairman should update his staff on the new policy.",
        "Each policeman must submit his report before the shift ends.",
        "The nurse said she would check on the patient.",
        "Every employee should bring his or her ID to the meeting.",
        "The fireman rushed into the burning building without hesitation.",
    ]

    for sent in test_sentences:
        result = make_counterfactual_pair(sent)
        print(f"Original : {result['original']}")
        print(f"Neutral  : {result['neutral_version']}")
        print(f"→ male   : {result['male_version']}")
        print(f"→ female : {result['female_version']}")
        print()

    pass


def main():
    test()


if __name__ == "__main__":
    main()
