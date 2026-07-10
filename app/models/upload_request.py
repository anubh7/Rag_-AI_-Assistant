from pydantic import BaseModel, Field
from typing import Optional


class UploadRequest(BaseModel):
    """Metadata that travels alongside a file upload (file itself comes via UploadFile)."""
    collection_name: Optional[str] = Field(
        default=None, description="Target Qdrant collection. Defaults to app default."
    )
    chunk_size: Optional[int] = Field(default=None, description="Override default chunk size.")
    chunk_overlap: Optional[int] = Field(default=None, description="Override default chunk overlap.")
