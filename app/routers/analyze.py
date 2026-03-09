from opencc import OpenCC
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.model_router import ModelRouter
from app.services.whitelist_engine import apply_whitelist  # ✅ 加這行

cc = OpenCC('s2t')

router = APIRouter()
model_router = ModelRouter()


class AnalyzeRequest(BaseModel):
    text: str


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
                "category": "tc_sc"  # ✅ 記得加分類
            })

    return errors


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text

    # ✅ 1️⃣ 繁簡檢測
    simplified_errors = detect_simplified(text)

    ai_errors = []

    # ✅ 2️⃣ AI 檢測
    try:
        ai_result = model_router.analyze(text)
        ai_errors = ai_result.get("errors", [])

        # ✅ 確保 AI 也有 category
        for err in ai_errors:
            err["category"] = "ai"

    except Exception as e:
        print("⚠ AI failed but system continues:", e)

    # ✅ 3️⃣ 合併
    all_errors = simplified_errors + ai_errors

    # ✅ 4️⃣ 白名單過濾
    filtered_errors = apply_whitelist(all_errors, text)

    return {
        "success": True,
        "errors": filtered_errors
    }