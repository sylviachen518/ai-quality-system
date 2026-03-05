from opencc import OpenCC
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.model_router import ModelRouter

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
                "reason": "簡體字，應改為繁體"
            })

    return errors


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):

    text = req.text

    # ✅ 1️⃣ 先做繁簡檢測（永遠執行）
    simplified_errors = detect_simplified(text)

    ai_errors = []

    # ✅ 2️⃣ 再嘗試 AI（就算失敗也不中止）
    try:
        ai_result = model_router.analyze(text)
        ai_errors = ai_result.get("errors", [])
    except Exception as e:
        print("⚠ AI failed but system continues:", e)

    # ✅ 3️⃣ 合併結果
    all_errors = simplified_errors + ai_errors

    return {
        "success": True,
        "errors": all_errors
    }