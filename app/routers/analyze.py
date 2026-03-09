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


# ✅ ✅ ✅ 香港專用極低誤判率 Prompt
HK_SYSTEM_PROMPT = """
你是一個專門為香港網站設計的繁體中文「錯誤檢測工具」。

你的任務是找出：

1. 錯別字
2. 明顯語法錯誤
3. 標點錯誤
4. 語意明顯不通順或動詞使用錯誤
5. 明顯缺字或漏字（導致語意不完整）

⚠️ 嚴格限制：

- 不要改寫句子
- 不要優化文筆
- 不要進行風格建議
- 不要將口語改為書面語
- 不要因為語氣問題提出修改
- 若句子雖然普通但語意完整，請不要修改

✅ 只有在「語意明顯不合理」時才提出修改。

✅如果動詞與受詞搭配在語義上明顯不合理，請指出。

✅ 以下屬於正確香港用語，絕對不要修改：
佢、咁、嚟、佗住、啲、喺、咗、冇、嘅、咩、
而家、邊個、點解、幾時、呢啲、嗰啲

✅ 請優先假設文章為香港本地寫作風格。

請回傳 JSON：

{
  "errors": [
    {
      "wrong": "...",
      "correct": "...",
      "reason": "..."
    }
  ]
}

若沒有錯誤，回傳：
{
  "errors": []
}
"""


def detect_simplified(text):
    errors = []
    converted = cc.convert(text)

    for i, (orig_char, conv_char) in enumerate(zip(text, converted)):
        if orig_char != conv_char:
            errors.append({
                "wrong": orig_char,
                "correct": conv_char,
                "start": i,
                "end": i + 1,
                "reason": "簡體字，應改為繁體",
                "category": "tc_sc"
            })

    return errors


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text

    # ✅ 1️⃣ 繁簡檢測
    simplified_errors = detect_simplified(text)

    ai_errors = []

    # ✅ 2️⃣ AI 檢測（香港模式）
    try:
        ai_result = model_router.analyze(
            text=text,
            system_prompt=HK_SYSTEM_PROMPT  # ✅ 傳入香港專用 prompt
        )

        raw_errors = ai_result.get("errors", [])

        # ✅ 防止 AI 回傳格式錯誤
        if isinstance(raw_errors, list):
            for err in raw_errors:
                if not isinstance(err, dict):
                    continue

                if "wrong" not in err or "correct" not in err:
                    continue

                err["category"] = "ai"
                ai_errors.append(err)

    except Exception as e:
        print("⚠ AI failed but system continues:", e)

    # ✅ 3️⃣ 合併錯誤
    all_errors = simplified_errors + ai_errors

    # ✅ 4️⃣ 白名單過濾（品牌 / 專有名詞等）
    filtered_errors = apply_whitelist(all_errors, text)

    return {
        "success": True,
        "errors": filtered_errors
    }