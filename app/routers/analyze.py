from opencc import OpenCC
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.model_router import ModelRouter
from app.services.whitelist_engine import apply_whitelist

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
⚠️不要因為語氣問題提出修改

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
3. 語義是否明顯不通

⚠️ 不要潤稿
⚠️ 只在語義明顯錯誤時指出

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
                "category": "tc_sc"
            })

    return errors


# ✅ AI 安全執行器（穩定 fallback）
def safe_ai_call(text, prompt, category):
    try:
        result = model_router.analyze(
            text=text,
            system_prompt=prompt
        )

        raw_errors = result.get("errors", [])
        clean = []

        if isinstance(raw_errors, list):
            for err in raw_errors:
                if not isinstance(err, dict):
                    continue

                if "wrong" not in err or "correct" not in err:
                    continue

                clean.append({
                    "wrong": err["wrong"],
                    "correct": err["correct"],
                    "reason": err.get("reason", ""),
                    "category": category
                })

        return clean

    except Exception as e:
        print(f"⚠ AI {category} failed:", e)
        return []


# ✅ 去重
def deduplicate_errors(errors):
    seen = set()
    unique = []

    for err in errors:
        key = (err.get("wrong"), err.get("correct"))
        if key not in seen:
            seen.add(key)
            unique.append(err)

    return unique


# ✅ 計算段落位置優先級
def compute_position_priority(text, error):
    wrong = error.get("wrong")
    if not wrong:
        return 99

    index = text.find(wrong)
    if index == -1:
        return 99

    # 標題（第一行）
    first_line_end = text.find("\n")
    if first_line_end == -1:
        first_line_end = len(text)

    if index <= first_line_end:
        return 0  # 最高優先

    # 首段（前 300 字）
    if index <= 300:
        return 1

    return 2


# ✅ 排序（類型 + 位置）
CATEGORY_PRIORITY = {
    "tc_sc": 0,
    "ai": 1,
    "semantic": 2
}


def sort_errors(errors, text):
    return sorted(
        errors,
        key=lambda e: (
            compute_position_priority(text, e),
            CATEGORY_PRIORITY.get(e.get("category"), 99)
        )
    )


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text

    # 1️⃣ 簡轉繁
    simplified_errors = detect_simplified(text)

    # 2️⃣ 嚴格 AI
    strict_errors = safe_ai_call(
        text,
        HK_STRICT_PROMPT,
        "ai"
    )

    # 3️⃣ 語義 AI
    semantic_errors = safe_ai_call(
        text,
        HK_SEMANTIC_PROMPT,
        "semantic"
    )

    # 4️⃣ 合併
    all_errors = simplified_errors + strict_errors + semantic_errors

    # 5️⃣ 去重
    all_errors = deduplicate_errors(all_errors)

    # 6️⃣ 排序（標題優先）
    all_errors = sort_errors(all_errors, text)

    # 7️⃣ 白名單過濾
    filtered_errors = apply_whitelist(all_errors, text)

    return {
        "success": True,
        "errors": filtered_errors
    }