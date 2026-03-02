from app.config import MODEL_PROVIDER
from .qwen_provider import QwenProvider
from .gemini_provider import GeminiProvider


class ModelRouter:

    def __init__(self):
        self.primary = QwenProvider() if MODEL_PROVIDER == "qwen" else GeminiProvider()
        self.fallback = GeminiProvider() if MODEL_PROVIDER == "qwen" else QwenProvider()

    def analyze(self, text: str) -> dict:
        try:
            return self.primary.analyze(text)

        except Exception as e:
            print("Primary model failed:", e)

            try:
                print("Switching to fallback model...")
                return self.fallback.analyze(text)

            except Exception as e2:
                print("Fallback also failed:", e2)
                return {
                    "errors": []
                }