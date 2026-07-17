"""
filter_builder — converts the incoming SearchFilters Pydantic model
(must / must_not / should with match / match_any conditions)
into a native qdrant_client.models.Filter object ready to pass
directly to Qdrant's search methods.

Filter semantics:
  must      → ALL conditions must be satisfied  (logical AND)
  must_not  → NONE of these conditions may be satisfied  (logical NOT)
  should    → AT LEAST ONE condition must be satisfied  (logical OR)

Condition types:
  match     → FieldCondition with MatchValue (exact equality)
  match_any → FieldCondition with MatchAny  (value in a list)
"""
from typing import List, Optional

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
)

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_field_condition(condition) -> Optional[FieldCondition]:
    """
    Convert a single FilterCondition object to a qdrant_client FieldCondition.
    Returns None if the condition is malformed (neither match nor match_any supplied).
    """
    key = condition.key

    if condition.match_any is not None:
        return FieldCondition(
            key=key,
            match=MatchAny(any=condition.match_any),
        )

    if condition.match is not None:
        return FieldCondition(
            key=key,
            match=MatchValue(value=condition.match),
        )

    logger.warning(
        f"FilterCondition for key '{key}' has neither 'match' nor 'match_any' — skipping."
    )
    return None


def _build_conditions(conditions) -> List[FieldCondition]:
    """Convert a list of FilterCondition objects, skipping any malformed ones."""
    built = []
    for cond in (conditions or []):
        fc = _build_field_condition(cond)
        if fc is not None:
            built.append(fc)
    return built


def build_qdrant_filter(filters) -> Optional[Filter]:
    """
    Convert a SearchFilters instance (or None) to a qdrant_client.models.Filter.

    Returns None when:
      - `filters` is None, or
      - all clauses are empty (no conditions provided at all).

    Usage:
        from app.retriever.filter_builder import build_qdrant_filter

        qdrant_filter = build_qdrant_filter(request.filters)
        # pass to similarity_search / hybrid_search
    """
    if filters is None:
        return None

    must_conditions = _build_conditions(filters.must)
    must_not_conditions = _build_conditions(filters.must_not)
    should_conditions = _build_conditions(filters.should)

    # No usable conditions → skip filter entirely
    if not (must_conditions or must_not_conditions or should_conditions):
        return None

    qdrant_filter = Filter(
        must=must_conditions or None,
        must_not=must_not_conditions or None,
        should=should_conditions or None,
    )

    logger.info(
        f"Built Qdrant filter — must:{len(must_conditions)}, "
        f"must_not:{len(must_not_conditions)}, should:{len(should_conditions)}"
    )
    return qdrant_filter
