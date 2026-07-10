"""
Simple in-memory chat history store, keyed by session_id.
Swap this out for a real DB (e.g. MySQL via SQLAlchemy) when persistence is needed —
the ChatService only depends on add_message()/get_history(), so the storage
backend can change without touching the rest of the app.
"""
from typing import Dict, List
from app.constants import ROLE_USER, ROLE_ASSISTANT
from app.utils.helper import utc_now_iso


class ChatHistory:
    _store: Dict[str, List[dict]] = {}

    def add_message(self, session_id: str, role: str, content: str):
        self._store.setdefault(session_id, [])
        self._store[session_id].append(
            {"role": role, "content": content, "timestamp": utc_now_iso()}
        )

    def get_history(self, session_id: str) -> List[dict]:
        return self._store.get(session_id, [])

    def clear_history(self, session_id: str):
        self._store.pop(session_id, None)
