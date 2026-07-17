from pydantic import BaseModel, Field
from typing import Optional, List, Any


class FilterCondition(BaseModel):
    """
    A single metadata filter condition applied to a Qdrant payload field.

    Exactly one of `match` or `match_any` should be provided per condition.

    Examples:
        - Exact match:    {"key": "source", "match": "hr_policy.pdf"}
        - Match any:      {"key": "author", "match_any": ["Alice", "Bob"]}
    """
    key: str = Field(..., description="Payload field name to filter on (e.g. 'source', 'file_type').")
    match: Optional[Any] = Field(default=None, description="Exact value the field must equal.")
    match_any: Optional[List[Any]] = Field(default=None, description="Field value must be one of these.")


class SearchFilters(BaseModel):
    """
    Qdrant filter specification.

    - must:      ALL conditions must match (logical AND).
    - must_not:  NONE of these conditions may match (logical NOT).
    - should:    AT LEAST ONE condition must match (logical OR).
    """
    must: Optional[List[FilterCondition]] = Field(default=None, description="All must be true (AND).")
    must_not: Optional[List[FilterCondition]] = Field(default=None, description="None may be true (NOT).")
    should: Optional[List[FilterCondition]] = Field(default=None, description="At least one must be true (OR).")


class ChatRequest(BaseModel):
    query: str = Field(..., description="User's question/message.")
    collection_name: Optional[str] = Field(default=None, description="Collection to retrieve from.")
    session_id: Optional[str] = Field(default="default", description="Chat session identifier for history.")
    top_k: Optional[int] = Field(default=None, description="Override number of chunks retrieved.")
    use_rag: bool = Field(default=True, description="Whether to ground the answer with retrieved context.")
    filters: Optional[SearchFilters] = Field(
        default=None,
        description=(
            "Optional Qdrant payload filters. Supports must/must_not/should clauses "
            "with match (exact) and match_any (list) conditions on document metadata fields."
        ),
    )
