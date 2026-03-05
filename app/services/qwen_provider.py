import json
import re
import requests
from .base_provider import BaseProvider
from app.config import QWEN_API_KEY


class QwenProvider(BaseProvider):

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

請回傳 JSON 格式：

{{
  "errors": [
    {{
      "wrong": "錯誤文字",
      "correct": "建議寫法",
      "start": 文字開始索引,
      "end": 文字結束索引,
      "reason": "錯誤原因"
    }}
  ]
}}

若沒有問題，回傳：
{{
  "errors": []
}}

文章：
{text}
"""

        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-max",
                "input": {
                    "prompt": prompt
                }
            },
            timeout=20
        )

        # ✅ 先檢查 HTTP 狀態碼
        if response.status_code != 200:
            raise Exception(f"Qwen API HTTP Error {response.status_code}: {response.text}")

        result = response.json()

        if "output" not in result:
            raise Exception(f"Unexpected API response: {result}")

        output = result["output"]

        if "text" not in output:
            raise Exception(f"No text returned: {result}")

        output_text = output["text"]

        # ✅ 抓 JSON 區塊
        match = re.search(r"\{.*\}", output_text, re.DOTALL)

        if not match:
            raise Exception(f"No JSON found in model response: {output_text}")

        json_str = match.group(0)

        try:
            return json.loads(json_str)
        except Exception:
            raise Exception(f"JSON parse failed: {json_str}")