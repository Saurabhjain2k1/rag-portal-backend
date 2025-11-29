from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list
