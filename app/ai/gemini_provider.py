from google import genai
from app.ai.base import AIProvider
from app.config import settings
# import os

class GeminiProvider(AIProvider):
    def __init__(self):
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing in environment variables.")

        self.client = genai.Client(api_key=api_key)
        self.chat_model = settings.gemini_chat_model
        self.embed_model = settings.gemini_embed_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts using Gemini.

        Uses the official `contents=` parameter and batch embedding.
        """
        if not texts:
            return []

        # Single call for all chunks (batch)
        resp = self.client.models.embed_content(
            model=self.embed_model,
            contents=texts,
        )

        # resp.embeddings is a list of embedding objects; each has `.values`
        vectors: list[list[float]] = [e.values for e in resp.embeddings]
        return vectors

    def chat(self, messages: list[dict]) -> str:
        lines: list[str] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prefix = "SYSTEM"
            elif role == "assistant":
                prefix = "ASSISTANT"
            else:
                prefix = "USER"
            lines.append(f"{prefix}: {content}")

        prompt = "\n".join(lines)

        resp = self.client.models.generate_content(
            model=self.chat_model,
            contents=prompt,
        )
        return resp.text
