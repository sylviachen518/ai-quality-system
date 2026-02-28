import requests
from .base_provider import BaseProvider
from app.config import GEMINI_API_KEY


class GeminiProvider(BaseProvider):

    def analyze(self, text: str) -> dict:
        prompt = f"""
Analyze the news article.

Return JSON only:
{{
  "score": 0-100,
  "issues": [],
  "suggestions": []
}}

Article:
{text}
"""

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            },
            timeout=20
        )

        result = response.json()

        output_text = result["candidates"][0]["content"]["parts"][0]["text"]

        return eval(output_text)