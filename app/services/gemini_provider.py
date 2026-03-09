import json
import re
import requests
from .base_provider import BaseProvider
from app.config import GEMINI_API_KEY


class GeminiProvider(BaseProvider):

    def analyze(self, text: str, system_prompt: str) -> dict:

        prompt = f"""
{system_prompt}

文章：
{text}
"""

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1/models/gemini-1.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1
            }
        }

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code != 200:
            raise Exception(
                f"Gemini API HTTP {response.status_code}: {response.text}"
            )

        result = response.json()

        try:
            output_text = (
                result["candidates"][0]
                ["content"]["parts"][0]["text"]
            )
        except Exception:
            raise Exception(f"Unexpected Gemini response: {result}")

        return self._safe_parse_json(output_text)

    # ✅ ✅ ✅ 強制 JSON 安全解析
    def _safe_parse_json(self, output_text: str) -> dict:

        # 1️⃣ 直接嘗試解析
        try:
            data = json.loads(output_text)
            return self._validate_structure(data)
        except Exception:
            pass

        # 2️⃣ 嘗試抓 JSON 區塊
        match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
                return self._validate_structure(data)
            except Exception:
                pass

        # 3️⃣ 最後保底（避免炸系統）
        print("⚠ Gemini returned invalid JSON. Fallback to empty errors.")
        return {"errors": []}

    def _validate_structure(self, data: dict) -> dict:

        if not isinstance(data, dict):
            return {"errors": []}

        errors = data.get("errors", [])

        if not isinstance(errors, list):
            return {"errors": []}

        clean_errors = []

        for err in errors:
            if not isinstance(err, dict):
                continue

            if "wrong" not in err or "correct" not in err:
                continue

            clean_errors.append({
                "wrong": str(err.get("wrong", "")),
                "correct": str(err.get("correct", "")),
                "reason": str(err.get("reason", ""))
            })

        return {"errors": clean_errors}