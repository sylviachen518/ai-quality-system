import json
import re
import requests
from .base_provider import BaseProvider
from app.config import QWEN_API_KEY


class QwenProvider(BaseProvider):

    def analyze(self, text: str) -> dict:
        prompt = f"""
請分析以下新聞內容品質。

請只回傳 JSON：
{{
  "score": 0-100,
  "issues": [],
  "suggestions": []
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

        choices = result["output"].get("choices")

        if not choices:
            raise ValueError(f"No choices returned: {result}")

        output_text = choices[0]["message"]["content"]

        match = re.search(r"\{.*\}", output_text, re.DOTALL)

        if not match:
            raise ValueError(f"No JSON found in model response: {output_text}")

        json_str = match.group(0)

        return json.loads(json_str)