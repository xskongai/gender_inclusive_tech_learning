#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/10/26
Description: cleaner
把原始文本规范化，去掉噪音，方例后续分块和嵌入
"""

import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    # 多余空白，换行，制表符  ->单个空格。
    return re.sub(r"\s+", " ", text).strip()


def normalize_unicode(text: str) -> str:
    """统一 Unicode 编码（如全角字符、特殊引号）。"""
    return unicodedata.normalize("NFKC", text)


def remove_urls(text: str) -> str:
    return re.sub(r"https?://S+|www\.\S+", "", text)


def remove_special_chars(text: str, keep_punct: bool = True) -> str:
    """
     去掉控制字符和非打印字符。
     keep_punct=True 时保留标点（对 NLP 任务很重要）。
     """
    if keep_punct:
        return re.sub(r"[^\w\s.,!?;:'\"-]", "", text)
    return re.sub(r"[^\w\s]", "", text)


def clean(text: str) -> str:
    """主入口：按顺序应用所有清洗步骤。"""
    text = normalize_unicode(text)
    text = remove_urls(text)
    text = normalize_whitespace(text)
    text = remove_special_chars(text)
    text = normalize_whitespace(text)

    return text


def clean_batch(texts: list[str]) -> list[str]:
    return [clean(t) for t in texts]


def test():
    samples = [
        "  The  chairman   should \t update his staff.  ",
        "Visit https://example.com for details about mankind.",
        "Each employee must submit\u00a0his\u00a0report by Friday.",
    ]
    for s in samples:
        print(f"IN : {repr(s)}")
        print(f"OUT: {repr(clean(s))}")
        print()


def main():
    test()


if __name__ == "__main__":
    main()
