# app/ai/__init__.py
from app.config import settings
from app.ai.base import AIProvider
from app.ai.gemini_provider import GeminiProvider

def get_ai_provider() -> AIProvider:
    provider = settings.ai_provider.lower()
    if provider == "gemini":
        return GeminiProvider()
    # elif provider == "openai":
    #     return OpenAIProvider()

    # default to gemini
    return GeminiProvider()
