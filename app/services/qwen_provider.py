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

        # ⚠ 這裡換成你實際千問 API endpoint
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

        result = response.json()

        if "output" not in result:
            raise ValueError(f"Unexpected API response: {result}")

        output = result.get("output", {})

        if "text" in output:
            output_text = output["text"]

        elif "choices" in output:
            output_text = output["choices"][0]["message"]["content"]

        else:
            raise ValueError(f"Unexpected API format: {result}")

        match = re.search(r"\{.*\}", output_text, re.DOTALL)

        if not match:
            raise ValueError(f"No JSON found in model response: {output_text}")

        json_str = match.group(0)

        return json.loads(json_str)