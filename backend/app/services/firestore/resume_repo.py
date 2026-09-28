import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class ResumeRepository:
    """Manages persistent resume metadata, ATS evaluations, and Storage paths in Firestore under users/{uid}/resumes/{id}."""

    @staticmethod
    def _collection_path(uid: str) -> str:
        return f"users/{uid}/resumes"

    @classmethod
    async def get_latest_resume(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch user's latest analyzed resume record."""
        docs = await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="created_at",
            descending=True,
            limit=1
        )
        return docs[0] if docs else None

    @classmethod
    async def get_resume(cls, uid: str, resume_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific resume record, strictly scoped to uid."""
        path = f"{cls._collection_path(uid)}/{resume_id}"
        return await FirestoreClient.get_document(path)

    @classmethod
    async def save_resume(cls, uid: str, resume_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new or updated resume analysis record."""
        path = f"{cls._collection_path(uid)}/{resume_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = resume_id
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def list_resumes(cls, uid: str) -> List[Dict[str, Any]]:
        """List all resumes for user."""
        return await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="created_at",
            descending=True
        )

    @classmethod
    async def delete_resume(cls, uid: str, resume_id: str) -> bool:
        """Delete resume record."""
        path = f"{cls._collection_path(uid)}/{resume_id}"
        return await FirestoreClient.delete_document(path)
