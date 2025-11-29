# app/ai/base.py
from abc import ABC, abstractmethod
from typing import List, Dict

class AIProvider(ABC):
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Return a list of embedding vectors for each input text."""
        raise NotImplementedError

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Chat completion: messages is a list of dicts:
        [{ "role": "system"|"user"|"assistant", "content": "..." }, ...]
        Returns assistant text.
        """
        raise NotImplementedError
