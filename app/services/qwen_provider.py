import json
import re
import requests
from .base_provider import BaseProvider
from app.config import QWEN_API_KEY


class QwenProvider(BaseProvider):

    def analyze(self, text: str, system_prompt: str) -> dict:

        prompt = f"""
{system_prompt}

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
                },
                "parameters": {
                    "temperature": 0.1
                }
            },
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(
                f"Qwen API HTTP {response.status_code}: {response.text}"
            )

        result = response.json()

        try:
            output_text = result["output"]["text"]
        except Exception:
            raise Exception(f"Unexpected Qwen response: {result}")

        return self._safe_parse_json(output_text)

    # ✅ ✅ ✅ 強制 JSON 安全解析
    def _safe_parse_json(self, output_text: str) -> dict:

        # 1️⃣ 直接解析
        try:
            data = json.loads(output_text)
            return self._validate_structure(data)
        except Exception:
            pass

        # 2️⃣ 抓 JSON 區塊
        match = re.search(r"\{.*\}", output_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
                return self._validate_structure(data)
            except Exception:
                pass

        # 3️⃣ 最終保底
        print("⚠ Qwen returned invalid JSON. Fallback to empty errors.")
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