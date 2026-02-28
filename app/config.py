import os

# 原本設定
AI_WEIGHT = 0.7
RULE_WEIGHT = 0.3

# 模型設定
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "qwen").lower()

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ 安全檢查
if MODEL_PROVIDER == "qwen" and not QWEN_API_KEY:
    raise ValueError("QWEN_API_KEY not set")

if MODEL_PROVIDER == "gemini" and not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set")