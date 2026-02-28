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

        # ⚠ 這裡依實際回傳格式取值
        output_text = result["output"]["text"]

        return eval(output_text)  # 建議之後改成 json.loads