from app.config import MODEL_PROVIDER
from .qwen_provider import QwenProvider
from .gemini_provider import GeminiProvider


class ModelRouter:

    def __init__(self):
        print(f"ModelRouter initialized. MODEL_PROVIDER = {MODEL_PROVIDER}")

        if MODEL_PROVIDER == "qwen":
            self.primary = QwenProvider()
            self.fallback = GeminiProvider()
        else:
            self.primary = GeminiProvider()
            self.fallback = QwenProvider()

    def analyze(self, text: str) -> dict:
        try:
            print("Calling primary model...")
            result = self.primary.analyze(text)
            print("Primary model success.")
            return result

        except Exception as e:
            print("Primary model error:", repr(e))

            try:
                print("Switching to fallback model...")
                result = self.fallback.analyze(text)
                print("Fallback model success.")
                return result

            except Exception as e2:
                print("Fallback model error:", repr(e2))

                # 🔥 關鍵：不要吞錯誤，直接丟出去
                raise Exception(
                    f"Both models failed. Primary error: {repr(e)} | Fallback error: {repr(e2)}"
                )