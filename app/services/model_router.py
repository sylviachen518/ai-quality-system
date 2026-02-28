from app.config import MODEL_PROVIDER
from .qwen_provider import QwenProvider
from .gemini_provider import GeminiProvider


def normalize_format(data: dict) -> dict:
    return {
        "score": int(data.get("score", 0)),
        "issues": list(data.get("issues", [])),
        "suggestions": list(data.get("suggestions", []))
    }


class ModelRouter:

    def __init__(self):
        self.primary = QwenProvider() if MODEL_PROVIDER == "qwen" else GeminiProvider()
        self.fallback = GeminiProvider() if MODEL_PROVIDER == "qwen" else QwenProvider()

    def analyze(self, text: str) -> dict:
        try:
            result = self.primary.analyze(text)
            return normalize_format(result)

        except Exception as e:
            print("Primary model failed:", e)

            try:
                print("Switching to fallback model...")
                result = self.fallback.analyze(text)
                return normalize_format(result)

            except Exception as e2:
                print("Fallback also failed:", e2)
                return {
                    "score": 0,
                    "issues": ["AI service unavailable"],
                    "suggestions": []
                }