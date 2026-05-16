#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/13/26
Description: inspector
语料质量检查
职责：在语料进入嵌入阶段之前，回答三个问题：
1.数量够不够 ？太少则检索效果差
2.长度分布合不合理？太长 太短 影响嵌入质量
3.还有没有明显的偏见词？语料本身要足够干净
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib
import importlib.util


def _get_data_module(name: str):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent.parent / "m01_data" / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_gender_pairs = _get_data_module("gender_pairs")

# 用于检测的偏见词列表（出现在语料里就是警告）
BIASED_WORDS = set(
    list(_gender_pairs.GENDER_TO_NEUTRAL.keys()) +
    [
        "mankind", "manpower", "stewardess", "actress", "waitress",
        "congressman", "chairwoman", "businessman"
    ]
)


def inspect(chunks: list, verbose: bool = True) -> dict:
    """对chunk 列表做全面检查，返回统计报告"""
    if not chunks:
        print("[inspector] 语料为空!")
        return {}

    texts = [c.text for c in chunks]
    lengths = [len(t) for t in texts]

    # basic statistics
    stats = {
        "total_chunks": len(chunks),
        "total_chars": sum(lengths),
        "avg_length": round(sum(lengths) / len(lengths), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "unique_sources": len(set(c.source.split("_")[0] + "_" + c.source.split("_")[1]
                                 if "_" in c.source else c.source
                                 for c in chunks
                                 ))

    }
    # length distribution
    buckets = {"<50": 0, "50-100": 0, "100-200": 0, "200-300": 0, ">300": 0}
    for l in lengths:
        if l < 50:
            buckets["<50"] += 1
        elif l < 100:
            buckets["50-100"] += 1
        elif l < 200:
            buckets["100-200"] += 1
        elif l < 300:
            buckets["200-300"] += 1
        else:
            buckets[">300"] += 1
    stats["length_distribution"] = buckets

    # bias check
    biased_chunks = []
    biased_word_counts: dict[str, int] = {}
    for c in chunks:
        words_in_text = set(c.text.lower().split())
        found = words_in_text & BIASED_WORDS
        if found:
            biased_chunks.append({"chunk": c.text[:80] + "...", "biased_words": list(found)})
            for w in found:
                biased_word_counts[w] = biased_word_counts.get(w, 0) + 1

    stats["biased_chunk_count"] = len(biased_chunks)
    stats["biased_word_freq"] = dict(
        sorted(biased_word_counts.items(), key=lambda x: -x[1])
    )
    # print report
    if verbose:
        print("=" * 50)
        print("  语料质量报告")
        print("=" * 50)
        print(f"  Chunk 总数    : {stats['total_chunks']}")
        print(f"  总字符数      : {stats['total_chars']:,}")
        print(f"  平均长度      : {stats['avg_length']} 字符")
        print(f"  长度范围      : {stats['min_length']} ~ {stats['max_length']}")
        print(f"  来源种类数    : {stats['unique_sources']}")
        print()
        print("  长度分布:")
        for bucket, count in buckets.items():
            bar = "█" * (count * 20 // max(buckets.values(), default=1))
            print(f"    {bucket:>8}  {bar} {count}")
        print()
        if biased_chunks:
            print(f"  检测到 {len(biased_chunks)} 个含偏见词的 Chunk")
            print(f"  高频偏见词: {dict(list(stats['biased_word_freq'].items())[:5])}")
            print()
            print("  示例（前 3 条）:")
            for item in biased_chunks[:3]:
                print(f"    词: {item['biased_words']}")
                print(f"    文: {item['chunk']}")
                print()
        else:
            print(" 未检测到明显偏见词")
        print("=" * 50)


def test():
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from corpus_builder import build_corpus

    chunks = build_corpus(use_builtin=True,strategy="sentence",save = False)
    stats = inspect(chunks,verbose = True)

def main():
    test()

if __name__ == "__main__":
    main()
