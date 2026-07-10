from pydantic import BaseModel
from typing import List, Optional


class SourceChunk(BaseModel):
    content: str
    source: Optional[str] = None
    score: Optional[float] = None
    metadata: Optional[dict] = None


class ChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[SourceChunk] = []
