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


# ✅ 加入 mode
class AnalyzeRequest(BaseModel):
    text: str
    mode: Optional[str] = "normal"   # normal / hk_strict


# ✅ ✅ 合併 AI 檢測 Prompt
HK_COMBINED_PROMPT = """
你是一個香港網站專用的繁體中文錯誤檢測工具。

請檢查以下錯誤：

【一】基礎錯誤
1. 錯別字
2. 明顯語法錯誤
3. 標點錯誤
4. 明顯缺字

【二】語義搭配錯誤
1. 動詞與受詞搭配不合理
2. 主詞與動作邏輯錯誤
3. 常見搭配錯誤（例如：來一個人生奇蹟）

⚠️ 不要潤稿
⚠️ 不要優化文筆
⚠️ 不要風格建議
⚠️ 不要將口語改為書面語
⚠️ 不要因為語氣問題提出修改
⚠️ 只指出錯誤

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


# ✅ ✅ 新增：找出所有出現位置
def find_all_occurrences(text, substring):
    start = 0
    positions = []

    while True:
        index = text.find(substring, start)
        if index == -1:
            break
        positions.append(index)
        start = index + len(substring)

    return positions


# ✅ 簡轉繁檢測（永遠執行）
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


# ✅ AI 呼叫（統一類型）
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

            # ✅ 改這裡：找全部出現位置
            positions = find_all_occurrences(text, wrong)

            for index in positions:
                clean.append({
                    "wrong": wrong,
                    "correct": correct,
                    "reason": err.get("reason", ""),
                    "start": index,
                    "end": index + len(wrong),
                    "category": category,
                    "priority": 80
                })

        return clean

    except Exception as e:
        print("AI failed:", e)
        return []


# ✅ 去重
def deduplicate_errors(errors):
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


# ✅ 分類排序優先級
CATEGORY_PRIORITY = {
    "tc_sc": 0,
    "rule": 1,
    "ai": 2
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

    simplified_errors = detect_simplified(text)
    rule_errors = apply_rules(text)

    ai_errors = []
    if mode == "hk_strict":
        ai_errors = safe_ai_call(
            text,
            HK_COMBINED_PROMPT,
            "ai"
        )

    all_errors = (
        simplified_errors +
        rule_errors +
        ai_errors
    )

    all_errors = deduplicate_errors(all_errors)
    all_errors = sort_errors(all_errors)
    filtered_errors = apply_whitelist(all_errors, text)

    return {
        "success": True,
        "mode": mode,
        "errors": filtered_errors
    }