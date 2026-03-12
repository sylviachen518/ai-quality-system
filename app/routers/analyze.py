from opencc import OpenCC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.model_router import ModelRouter
from app.services.whitelist_engine import apply_whitelist
from app.services.rule_engine import apply_rules

cc = OpenCC('s2t')

router = APIRouter()
model_router = ModelRouter()


# ✅ ✅ 加入 mode
class AnalyzeRequest(BaseModel):
    text: str
    mode: Optional[str] = "normal"   # normal / hk_strict


# ✅ 主校對模式（保守）
HK_STRICT_PROMPT = """
你是一個香港網站專用的繁體中文錯誤檢測工具。

請檢查：
1. 錯別字
2. 明顯語法錯誤
3. 標點錯誤
4. 明顯缺字

⚠️ 不要潤稿
⚠️ 不要優化文筆
⚠️ 不要風格建議
⚠️ 不要將口語改為書面語
⚠️ 不要因為語氣問題提出修改

請回傳 JSON:
{
  "errors": [
    {
      "wrong": "...",
      "correct": "...",
      "reason": "..."
    }
  ]
}

若無錯誤:
{
  "errors": []
}
"""


# ✅ 語義檢測模式
HK_SEMANTIC_PROMPT = """
你是一個語義搭配檢測工具。

請檢查：
1. 動詞與受詞搭配是否不合理
2. 主詞與動作邏輯是否錯誤
3. 常見搭配錯誤（例如：來一個人生奇蹟）

⚠️ 即使不是語法錯誤，只要搭配不自然，也要指出
⚠️ 不要潤稿
⚠️ 只回傳錯誤

請回傳 JSON:
{
  "errors": [
    {
      "wrong": "...",
      "correct": "...",
      "reason": "語義不合理"
    }
  ]
}

若無錯誤:
{
  "errors": []
}
"""


# ✅ 簡轉繁檢測
def detect_simplified(text):
    errors = []
    converted = cc.convert(text)

    for i, (orig, conv) in enumerate(zip(text, converted)):
        if orig != conv:
            errors.append({
                "wrong": orig,
                "correct": conv,
                "start": i,
                "end": i + 1,
                "reason": "簡體字",
                "category": "tc_sc",
                "priority": 0
            })

    return errors


# ✅ AI 呼叫
def safe_ai_call(text, prompt, category):
    try:
        result = model_router.analyze(
            text=text,
            system_prompt=prompt
        )

        raw_errors = result.get("errors", [])
        clean = []

        for err in raw_errors:
            if not isinstance(err, dict):
                continue

            wrong = err.get("wrong")
            correct = err.get("correct")

            if not wrong or not correct:
                continue

            index = text.find(wrong)

            if index == -1:
                continue

            clean.append({
                "wrong": wrong,
                "correct": correct,
                "reason": err.get("reason", ""),
                "start": index,
                "end": index + len(wrong),
                "category": category,
                "priority": 80 if category == "ai" else 90
            })

        return clean

    except Exception as e:
        print("AI failed:", e)
        return []


# ✅ ✅ 升級版去重（安全處理 None）
def deduplicate_errors(errors):
    # 先過濾沒有 start 的（避免排序炸掉）
    errors = [e for e in errors if e.get("start") is not None]

    errors = sorted(
        errors,
        key=lambda x: (
            x.get("start", 999999),
            -(x.get("end", 0) - x.get("start", 0))
        )
    )

    filtered = []

    for err in errors:
        overlap = False
        for f in filtered:
            if err["start"] >= f["start"] and err["end"] <= f["end"]:
                overlap = True
                break
        if not overlap:
            filtered.append(err)

    return filtered


# ✅ 排序優先級
CATEGORY_PRIORITY = {
    "tc_sc": 0,
    "rule": 1,
    "ai": 2,
    "semantic": 3
}


def sort_errors(errors):
    return sorted(
        errors,
        key=lambda e: (
            e.get("start", 999999),
            e.get("priority", 99),
            CATEGORY_PRIORITY.get(e.get("category"), 99)
        )
    )


# ✅ ✅ ✅ 主 API
@router.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text
    mode = req.mode or "normal"

    # =========================
    # 1️⃣ 簡轉繁檢查（永遠執行）
    # =========================
    simplified_errors = detect_simplified(text)

    # =========================
    # 2️⃣ Rule engine（永遠執行）
    # =========================
    rule_errors = apply_rules(text)

    # =========================
    # 3️⃣ 嚴格 AI（只在 hk_strict 模式）
    # =========================
    strict_errors = []
    if mode == "hk_strict":
        strict_errors = safe_ai_call(
            text,
            HK_STRICT_PROMPT,
            "ai"
        )

    # =========================
    # 4️⃣ 語義 AI（永遠執行）
    # =========================
    semantic_errors = safe_ai_call(
        text,
        HK_SEMANTIC_PROMPT,
        "semantic"
    )

    # =========================
    # 5️⃣ 合併
    # =========================
    all_errors = (
        simplified_errors +
        rule_errors +
        strict_errors +
        semantic_errors
    )

    # =========================
    # 6️⃣ 去重
    # =========================
    all_errors = deduplicate_errors(all_errors)

    # =========================
    # 7️⃣ 排序
    # =========================
    all_errors = sort_errors(all_errors)

    # =========================
    # 8️⃣ 白名單
    # =========================
    filtered_errors = apply_whitelist(all_errors, text)

    return {
        "success": True,
        "mode": mode,
        "errors": filtered_errors
    }