from pydantic import BaseModel, Field
from typing import Optional


class CollectionRequest(BaseModel):
    collection_name: str = Field(..., description="Name of the Qdrant collection.")
    vector_size: Optional[int] = Field(default=None, description="Embedding dimension override.")
