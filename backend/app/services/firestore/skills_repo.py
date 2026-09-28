import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class SkillsRepository:
    """Manages persistent skills and evidence in Firestore under users/{uid}/skills/{skill_id}."""

    @staticmethod
    def _collection_path(uid: str) -> str:
        return f"users/{uid}/skills"

    @classmethod
    async def list_skills(cls, uid: str) -> List[Dict[str, Any]]:
        """List all verified and gap skills for user."""
        return await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="proficiency_percent",
            descending=True
        )

    @classmethod
    async def get_skill(cls, uid: str, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get single skill by ID."""
        path = f"{cls._collection_path(uid)}/{skill_id}"
        return await FirestoreClient.get_document(path)

    @classmethod
    async def save_skill(cls, uid: str, skill_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update skill."""
        path = f"{cls._collection_path(uid)}/{skill_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = skill_id
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        if "evidences" not in payload:
            payload["evidences"] = []
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def upsert_skill_by_name(cls, uid: str, skill_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Find skill by name and update, or create a new skill entry."""
        skills = await cls.list_skills(uid)
        norm_name = skill_name.strip().lower()
        matched = next((s for s in skills if s.get("skill_name", "").strip().lower() == norm_name), None)
        import uuid
        skill_id = matched["id"] if matched and "id" in matched else str(uuid.uuid4())
        payload = dict(data)
        payload["skill_name"] = skill_name
        payload["normalized_name"] = norm_name
        return await cls.save_skill(uid, skill_id, payload)


    @classmethod
    async def add_evidence(cls, uid: str, skill_id: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Add an evidence item to a skill."""
        skill = await cls.get_skill(uid, skill_id)
        if not skill:
            return {}
        evidences = skill.get("evidences", [])
        evidence_clean = dict(evidence)
        if "created_at" not in evidence_clean:
            evidence_clean["created_at"] = datetime.datetime.utcnow().isoformat()
        evidences.append(evidence_clean)
        return await cls.save_skill(uid, skill_id, {"evidences": evidences})

    @classmethod
    async def delete_skill(cls, uid: str, skill_id: str) -> bool:
        """Delete skill."""
        path = f"{cls._collection_path(uid)}/{skill_id}"
        return await FirestoreClient.delete_document(path)
