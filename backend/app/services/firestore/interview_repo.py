import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class InterviewRepository:
    """Manages adaptive mock interview sessions and evaluations in Firestore under users/{uid}/interview_sessions/{id}."""

    @staticmethod
    def _collection_path(uid: str) -> str:
        return f"users/{uid}/interview_sessions"

    @classmethod
    async def get_session(cls, uid: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch an interview session scoped strictly to user."""
        path = f"{cls._collection_path(uid)}/{session_id}"
        return await FirestoreClient.get_document(path)

    @classmethod
    async def save_session(cls, uid: str, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update interview session."""
        path = f"{cls._collection_path(uid)}/{session_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = session_id
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def list_sessions(cls, uid: str, completed_only: bool = False) -> List[Dict[str, Any]]:
        """List user's interview sessions, sorted by date."""
        filters = [("is_completed", "==", True)] if completed_only else None
        return await FirestoreClient.query_collection(
            cls._collection_path(uid),
            filters=filters,
            order_by="created_at",
            descending=True
        )

    @classmethod
    async def get_latest_session(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Get the most recent interview session for user."""
        docs = await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="created_at",
            descending=True,
            limit=1
        )
        return docs[0] if docs else None
