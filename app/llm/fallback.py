class FallbackLLM:
    """Lightweight LLM stub used when no provider credentials are configured.

    This keeps the app usable in local/test environments without crashing on import or
    on the first chat call when API keys are deliberately unset.
    """

    def __init__(self, provider: str = "gemini"):
        self.provider = provider.lower()

    def invoke(self, messages):
        payload = messages
        if isinstance(messages, list):
            last = messages[-1]
            if isinstance(last, dict):
                payload = last.get("content") or last.get("text") or str(last)
            else:
                payload = str(last)

        text = str(payload)
        if not text.strip():
            text = "No input was provided."

        return type("DummyResponse", (), {"content": f"I can't answer right now because no {self.provider} API key is configured for this app. "
                                                    f"Please add the required credentials in your .env file.\n\nUser question: {text}"})()

    async def ainvoke(self, messages):
        return self.invoke(messages)
