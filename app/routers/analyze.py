from opencc import OpenCC
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.model_router import ModelRouter
from app.services.whitelist_engine import apply_whitelist
from app.services.rule_engine import apply_rules

cc = OpenCC('s2t')

router = APIRouter()
model_router = ModelRouter()


class AnalyzeRequest(BaseModel):
    text: str


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


# ✅ 語義檢測模式（專抓動詞搭配）
HK_SEMANTIC_PROMPT = """
你是一個語義搭配檢測工具。

請檢查：
1. 動詞與受詞搭配是否不合理
2. 主詞與動作邏輯是否錯誤
3. 常見搭配錯誤（例如：來一個人生奇蹟）

⚠️ 即使不是語法錯誤，只要搭配不自然，也要指出
⚠️ 不要潤稿
⚠️ 只回傳錯誤，不要建議多種寫法

例如：
- 來一個人生奇蹟（應為迎來）
- 吃機會
- 打希望

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

            clean.append({
                "wrong": wrong,
                "correct": correct,
                "reason": err.get("reason", ""),
                "start": index if index != -1 else None,
                "end": index + len(wrong) if index != -1 else None,
                "category": category,
                "priority": 80 if category == "ai" else 90
            })

        return clean

    except Exception as e:
        print("AI failed:", e)
        return []


# ✅ 去重
def deduplicate_errors(errors):
    seen = set()
    unique = []

    for err in errors:
        key = (err.get("start"), err.get("wrong"))
        if key not in seen:
            seen.add(key)
            unique.append(err)

    return unique


# ✅ 排序（位置 + rule priority + 類型）
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
            e.get("start", 99999),
            e.get("priority", 99),
            CATEGORY_PRIORITY.get(e.get("category"), 99)
        )
    )


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text

    # 1️⃣ 簡轉繁
    simplified_errors = detect_simplified(text)

    # 2️⃣ Rule engine
    rule_errors = apply_rules(text)

    # 3️⃣ 嚴格 AI
    strict_errors = safe_ai_call(text, HK_STRICT_PROMPT, "ai")

    # 4️⃣ 語義 AI
    semantic_errors = safe_ai_call(text, HK_SEMANTIC_PROMPT, "semantic")

    # 5️⃣ 合併
    all_errors = (
        simplified_errors +
        rule_errors +
        strict_errors +
        semantic_errors
    )

    # 6️⃣ 去重
    all_errors = deduplicate_errors(all_errors)

    # 7️⃣ 排序
    all_errors = sort_errors(all_errors)

    # 8️⃣ 白名單
    filtered_errors = apply_whitelist(all_errors, text)

    return {
        "success": True,
        "errors": filtered_errors
    }
