import os
from dotenv import load_dotenv

# ✅ 讀取 .env（本地用）
load_dotenv()

# 權重設定
AI_WEIGHT = 0.7
RULE_WEIGHT = 0.3

# 模型設定
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "qwen").lower()

QWEN_API_KEY = os.getenv("QWEN_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ 不要 raise
# ✅ 只給警告
if MODEL_PROVIDER == "qwen" and not QWEN_API_KEY:
    print("⚠ Warning: QWEN_API_KEY not set")

if MODEL_PROVIDER == "gemini" and not GEMINI_API_KEY:
    print("⚠ Warning: GEMINI_API_KEY not set")