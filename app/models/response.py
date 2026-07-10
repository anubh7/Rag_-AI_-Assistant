from pydantic import BaseModel
from typing import Any, Optional


class APIResponse(BaseModel):
    """Generic envelope used across all endpoints for consistent responses."""
    status: str
    message: str
    data: Optional[Any] = None
