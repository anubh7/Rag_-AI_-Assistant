from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    query: str = Field(..., description="User's question/message.")
    collection_name: Optional[str] = Field(default=None, description="Collection to retrieve from.")
    session_id: Optional[str] = Field(default="default", description="Chat session identifier for history.")
    top_k: Optional[int] = Field(default=None, description="Override number of chunks retrieved.")
    use_rag: bool = Field(default=True, description="Whether to ground the answer with retrieved context.")
