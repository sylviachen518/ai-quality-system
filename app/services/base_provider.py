class BaseProvider:
    def analyze(self, text: str) -> dict:
        raise NotImplementedError