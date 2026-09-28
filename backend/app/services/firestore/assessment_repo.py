import uuid
import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class AssessmentRepository:
    """Manages persistent Career Assessment data in Firestore under users/{uid}/assessment_responses/{id}."""

    @staticmethod
    def _collection_path(uid: str) -> str:
        return f"users/{uid}/assessment_responses"

    @classmethod
    async def get_latest_assessment(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Get the most recent assessment for user."""
        docs = await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="updated_at",
            descending=True,
            limit=1
        )
        return docs[0] if docs else None

    @classmethod
    async def get_latest_completed_assessment(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Get the most recent completed assessment for user."""
        docs = await FirestoreClient.query_collection(
            cls._collection_path(uid),
            filters=[("status", "==", "COMPLETED")],
            order_by="updated_at",
            descending=True,
            limit=1
        )
        return docs[0] if docs else None

    @classmethod
    async def has_completed_assessment(cls, uid: str) -> bool:
        """Check if user has any completed assessment."""
        completed = await cls.get_latest_completed_assessment(uid)
        return completed is not None and completed.get("ai_analysis_json") is not None

    @classmethod
    async def get_assessment(cls, uid: str, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific assessment response."""
        path = f"{cls._collection_path(uid)}/{assessment_id}"
        return await FirestoreClient.get_document(path)

    @classmethod
    async def save_assessment(cls, uid: str, assessment_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update an assessment session."""
        path = f"{cls._collection_path(uid)}/{assessment_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = assessment_id
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def list_assessments(cls, uid: str) -> List[Dict[str, Any]]:
        """List all assessments for user."""
        return await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="created_at",
            descending=True
        )
