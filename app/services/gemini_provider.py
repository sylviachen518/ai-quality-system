import json
import re
import requests
from .base_provider import BaseProvider
from app.config import GEMINI_API_KEY


class GeminiProvider(BaseProvider):

    def analyze(self, text: str) -> dict:

        prompt = f"""
你是一位專業的繁體中文校對專家。

請檢查以下文章是否存在：

1. 用詞錯誤
2. 不自然搭配
3. 語意不完整
4. 重複詞語
5. 語法問題

⚠ 不需要檢查簡體字（已由系統處理）

請只回傳 JSON：

{{
  "errors": [
    {{
      "wrong": "錯誤文字",
      "correct": "建議寫法",
      "start": 0,
      "end": 0,
      "reason": "錯誤原因"
    }}
  ]
}}

若沒有錯誤請回傳：
{{
  "errors": []
}}

文章：
{text}
"""

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        response = requests.post(url, json=payload, timeout=20)

        # ✅ 先檢查 HTTP 狀態碼
        if response.status_code != 200:
            raise Exception(f"Gemini API HTTP {response.status_code}: {response.text}")

        result = response.json()

        if "candidates" not in result:
            raise Exception(f"Unexpected Gemini response: {result}")

        output_text = result["candidates"][0]["content"]["parts"][0]["text"]

        # ✅ 抓 JSON 區塊
        match = re.search(r"\{.*\}", output_text, re.DOTALL)

        if not match:
            raise Exception(f"No JSON found in Gemini output: {output_text}")

        json_str = match.group(0)

        try:
            return json.loads(json_str)
        except Exception:
            raise Exception(f"Gemini JSON parse failed: {json_str}")