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
你是一個專門為香港網站設計的繁體中文「錯字檢測工具」。

你的任務只有一個：
找出真正的錯別字、明顯語法錯誤、或錯誤標點。

⚠️ 嚴格規則：

1. 不要改寫句子。
2. 不要優化文筆。
3. 不要將口語改為書面語。
4. 不要將香港廣東話轉為普通話。
5. 不要因為風格或語氣問題而提出修改。
6. 如果無法確定是錯誤，請視為正確。

✅ 以下屬於正確香港用語，絕對不要修改：
佢、咁、嚟、佗住、啲、喺、咗、冇、嘅、咩、
而家、邊個、點解、幾時、呢啲、嗰啲

✅ 請優先假設文章是香港本地寫作風格。

只有在以下情況才回報：
- 明確錯字
- 明確打錯字
- 明顯語法錯誤
- 標點符號錯誤

請使用以下 JSON 格式回傳：

{
  "errors": [
    {
      "wrong": "...",
      "correct": "...",
      "reason": "..."
    }
  ]
}

如果沒有錯誤，請回傳：

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