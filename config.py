#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Kong Xiaoshuang
Date: 5/10/26
Description: config
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 从.env 文件 读取 APENAI_API_KEY 等敏感信息


# 项目根目录：config.py 所在目录
ROOT = Path(__file__).resolve().parent

# .env 路径
ENV_PATH = ROOT / ".env"

# 显式读取项目根目录下的 .env
loaded = load_dotenv(dotenv_path=ENV_PATH, override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()


def mask_key(k: str) -> str:
    if not k:
        return "EMPTY"
    return f"len={len(k)}, prefix={k[:10]}, suffix={k[-4:]}"


# 临时调试：确认到底读了哪个 .env
print(f"[config] config.py 路径: {Path(__file__).resolve()}")
print(f"[config] .env 路径: {ENV_PATH}")
print(f"[config] .env 是否存在: {ENV_PATH.exists()}")
print(f"[config] load_dotenv 是否成功: {loaded}")
print(f"[config] OPENAI_API_KEY: {mask_key(OPENAI_API_KEY)}")

# path
ROOT = Path(__file__).parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
INDEX_DIR = ROOT / "data" / "index"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# LLM
LLM_MODEL = "gpt-4o-mini"  # 实验用小模型，省token 换 gpt-4o可更准
LLM_TEMPERATURE = 0.0  # 评估、去偏任务保证稳定性

# embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # sentence-BER
EMBEDDING_DIM = 384  # T，本地运行，无需 API

# chunk parameters
CHUNK_SIZE = 200
CHUNK_OVERLAP = 40

# RAG
TOP_K = 5

# EVALUATE
EVAL_METRICS = ["gender_assumption", "gender_neutrality", "quality_relevance"]
EVAL_SCALE = 5


def main():
    pass


if __name__ == "__main__":
    main()
