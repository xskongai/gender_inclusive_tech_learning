#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/12/26
Description: loader

m02_corpus/loader.py — 语料加载
职责：从不同来源读取原始文本，统一返回 List[{"text": str, "source": str}]
支持：
  - 纯文本文件 (.txt)
  - Excel 词对表 (.xlsx)  ← 对应论文的 Gender Neutral Pairs.xlsx / CF Rules.xlsx
  - 内置样本语料           ← 没有真实文件时用于快速调试
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# 类型别名
Doc = dict

# 内置样本语料
# 这些句子都是包容性写法，是 RAG检索时的参考内容。
# 真实项目里 这里会是几千条来自数据集的文本
BUILTIN_INCLUSIVE_CORPUS = [
    # 职场场景
    "The chairperson called the meeting to order and asked each team member to share their update.",
    "Every employee is required to submit their timesheet by the end of the week.",
    "The firefighter arrived on the scene and immediately began assessing the situation.",
    "A police officer should treat every citizen with respect, regardless of their background.",
    "The spokesperson confirmed that the organization would release a statement later in the day.",
    "Each team member brought their unique perspective to the discussion.",
    "The manager asked the staff to coordinate their schedules for the upcoming project.",
    # 医疗场景
    "The nurse reviewed the patient's chart and noted any changes in their condition.",
    "Every doctor should communicate clearly with their patients about treatment options.",
    "The surgeon briefed their team before entering the operating room.",
    "A healthcare provider should respect the privacy of each of their patients.",
    # 教育场景
    "Each student should feel comfortable expressing their opinions in class.",
    "The teacher encouraged every learner to pursue their academic goals.",
    "A principal must ensure their school provides a safe environment for all students.",
    "Every researcher should cite their sources accurately in academic work.",
    # 法律场景
    "The lawyer advised their client to remain silent until further notice.",
    "A judge must consider all evidence before delivering their verdict.",
    "Every witness has the right to have their testimony heard in court.",
    # 日常场景
    "A person should feel free to express their identity without fear of judgment.",
    "Each individual deserves to be treated with dignity and respect.",
    "Someone left their umbrella on the train; they should contact lost and found.",
    "Every child has the right to receive quality education in their community.",
    "The author published their first novel after years of dedicated writing.",
    "A pilot must complete their pre-flight checklist before every departure.",
    "The engineer presented their design to the review committee.",
    "Each athlete trained hard to improve their personal best.",
    "The journalist filed their report before the evening deadline.",
    "A chef must ensure their kitchen meets all health and safety standards.",
]

# WinoBias 风格样本：职业代词去偏后的版本
BUILTIN_WINOBIAS_NEUTRAL = [
    "The physician told the patient that they would need to schedule a follow-up appointment.",
    "The nurse said they would administer the medication after lunch.",
    "The construction worker finished their shift and headed home.",
    "The receptionist greeted each visitor and asked them to sign in.",
    "The accountant reviewed their client's financial statements carefully.",
    "The programmer stayed late to debug the issue in their code.",
    "The librarian helped the student find the books they were looking for.",
    "The housekeeper made sure every room was cleaned before the guests arrived.",
    "The cook prepared a meal that satisfied every diner's dietary needs.",
    "The analyst presented their quarterly findings to the board.",
]


def load_builtin(corpus_type: str = "inclusive") -> list[Doc]:
    """
    加载内置样本语料
    corpus_type: "inclusive" | "winobias"
    """
    if corpus_type == "inclusive":
        texts = BUILTIN_INCLUSIVE_CORPUS
        source_prefix = "builtin_inclusive"
    elif corpus_type == "winobias":
        texts = BUILTIN_WINOBIAS_NEUTRAL
        source_prefix = "builtin_winobias"
    else:
        raise ValueError(f"Unknown corpus_type:{corpus_type}")

    return [
        {
            "text": t,
            "source": f"{source_prefix}_{i}"
        }
        for i, t in enumerate(texts)
    ]


def load_txt(path: str | Path) -> list[Doc]:
    """
    从 .txt 文件加载语料
    格式假设：每行一个句子/段落，空行忽略
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found:{path}")

    docs = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                docs.append({"text": line, "source": f"{path.stem}_line{i}"})
    return docs


def load_xlsx_pairs(path: str | Path, text_col: str = "neutral") -> list[Doc]:
    """
    从 excel词对表加载语料。
    对应的论文的 Gender neutral pairs.xlsx
    text_col: 要读取的列名
    """
    if not HAS_PANDAS:
        raise ImportError("pandas not installed, please run pip install pandas ")

    path = Path(path)
    df = pd.read_excel(path)

    if text_col not in df.columns:
        raise ValueError(f"column {text_col} not exists, current columns {list(df.columns)} ")

    docs = []
    for i, row in df.iterrows():
        text = str(row[text_col]).strip()
        if text and text != "nan":
            docs.append({"text": text, "source": f"{path.stem}_row{i}"})


def load_all(
        txt_paths: list[str | Path] | None = None,
        xlsx_paths: list[str | Path] | None = None,
        use_builtin: bool = True,
) -> list[Doc]:
    """
    主入口：把所有来源合并成一个列表
    没有真实数据文件时，use_builtin = True 保证系统可以跑通
    """
    docs = []

    if use_builtin:
        docs.extend(load_builtin("inclusive"))
        docs.extend(load_builtin("winobias"))

    for p in (txt_paths or []):
        docs.extend(load_txt(p))

    for p in (xlsx_paths or []):
        docs.extend(load_xlsx_pairs(p))

    print(f"[loader]共加载{len(docs)}条原始文档")

    return docs


def test():
    docs = load_all(use_builtin=True)
    print(f"总计: {len(docs)} 条")
    print("\n前 3 条示例:")
    for d in docs[:3]:
        print(f"  [{d['source']}] {d['text']}")


def main():
    test()


if __name__ == "__main__":
    main()
