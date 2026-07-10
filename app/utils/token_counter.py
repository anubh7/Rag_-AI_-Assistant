"""
Token counting helper (used for chunking / context-window budgeting).
"""
try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENC = None


def count_tokens(text: str) -> int:
    if _ENC:
        return len(_ENC.encode(text))
    # Fallback rough estimate: ~4 chars per token
    return max(1, len(text) // 4)
