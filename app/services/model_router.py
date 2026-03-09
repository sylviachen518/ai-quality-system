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

    def analyze(self, text: str, system_prompt: str) -> dict:
        """
        text: 使用者文章
        system_prompt: 校對規則（例如香港嚴格模式）
        """

        try:
            print("Calling primary model...")
            result = self.primary.analyze(
                text=text,
                system_prompt=system_prompt
            )
            print("Primary model success.")
            return result

        except Exception as e:
            print("Primary model error:", repr(e))

            try:
                print("Switching to fallback model...")
                result = self.fallback.analyze(
                    text=text,
                    system_prompt=system_prompt
                )
                print("Fallback model success.")
                return result

            except Exception as e2:
                print("Fallback model error:", repr(e2))

                raise Exception(
                    f"Both models failed. "
                    f"Primary error: {repr(e)} | "
                    f"Fallback error: {repr(e2)}"
                )