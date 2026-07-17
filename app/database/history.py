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
    def add_message(self, db, session_id: str, role: str, content: str, user_id: int = None):
        """
        Add a message to the chat history. Creates the ChatSession if it doesn't exist.
        """
        from app.database.models import ChatSession, Message
        
        # Ensure session exists
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            if not user_id:
                raise ValueError("user_id is required to create a new chat session")
            title = content[:40] + "..." if len(content) > 40 else content
            session = ChatSession(id=session_id, user_id=user_id, title=title)
            db.add(session)
            db.commit()
            db.refresh(session)
        elif role == "user" and session.title.startswith("New Chat"):
            # Update title to first user message if it has a default title
            session.title = content[:40] + "..." if len(content) > 40 else content
            db.commit()

        # Save the message
        db_message = Message(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(db_message)
        db.commit()

    def get_history(self, db, session_id: str) -> List[dict]:
        """
        Fetch all messages in chronological order for a session.
        """
        from app.database.models import Message
        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.timestamp.asc())
            .all()
        )
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]

    def clear_history(self, db, session_id: str):
        """
        Delete a session and all its messages.
        """
        from app.database.models import ChatSession
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        db.commit()

    def get_user_sessions(self, db, user_id: int) -> List[dict]:
        """
        Fetch all chat sessions for a user, ordered by creation time.
        """
        from app.database.models import ChatSession
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )
        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat()
            }
            for s in sessions
        ]

