import datetime
from typing import Optional, Dict, Any
from app.services.firestore.client import FirestoreClient


class UserRepository:
    """Manages persistent User & Profile data in Firestore under /users/{uid}."""

    @staticmethod
    def _user_path(uid: str) -> str:
        return f"users/{uid}"

    @classmethod
    async def get_user(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile and account document."""
        return await FirestoreClient.get_document(cls._user_path(uid))

    @classmethod
    async def upsert_user(cls, uid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update user profile document."""
        now = datetime.datetime.utcnow().isoformat()
        payload = dict(data)
        payload["uid"] = uid
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        return await FirestoreClient.set_document(cls._user_path(uid), payload, merge=True)

    @classmethod
    async def update_target_career(cls, uid: str, target_career: str, archetype: Optional[str] = None) -> Dict[str, Any]:
        """Update target career and archetype."""
        payload = {
            "target_career": target_career,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        if archetype:
            payload["primary_archetype"] = archetype
        return await FirestoreClient.set_document(cls._user_path(uid), payload, merge=True)

    @classmethod
    async def set_assessment_completed(cls, uid: str, completed: bool = True) -> Dict[str, Any]:
        """Update assessment completion status."""
        payload = {
            "has_completed_assessment": completed,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        return await FirestoreClient.set_document(cls._user_path(uid), payload, merge=True)

    @classmethod
    async def get_user_profile(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile fields."""
        user = await cls.get_user(uid)
        return user.get("profile") if user and "profile" in user else user

    @classmethod
    async def update_user_profile(cls, uid: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile section."""
        now = datetime.datetime.utcnow().isoformat()
        payload = {
            "profile": profile_data,
            "updated_at": now
        }
        for k in ["target_career", "primary_archetype", "job_readiness_score", "skills_matrix", "recommended_roles"]:
            if k in profile_data:
                payload[k] = profile_data[k]
        return await FirestoreClient.set_document(cls._user_path(uid), payload, merge=True)

