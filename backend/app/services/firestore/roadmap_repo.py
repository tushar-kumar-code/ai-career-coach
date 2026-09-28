import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class RoadmapRepository:
    """Manages personalized learning roadmaps in Firestore under users/{uid}/roadmaps/{roadmap_id}."""

    @staticmethod
    def _collection_path(uid: str) -> str:
        return f"users/{uid}/roadmaps"

    @classmethod
    async def get_active_roadmap(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch the user's active roadmap."""
        docs = await FirestoreClient.query_collection(
            cls._collection_path(uid),
            filters=[("is_active", "==", True)],
            order_by="created_at",
            descending=True,
            limit=1
        )
        if docs:
            return docs[0]
        # Fallback to latest roadmap regardless of flag
        all_docs = await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="created_at",
            descending=True,
            limit=1
        )
        return all_docs[0] if all_docs else None

    @classmethod
    async def get_roadmap(cls, uid: str, roadmap_id: str) -> Optional[Dict[str, Any]]:
        """Fetch roadmap by ID."""
        path = f"{cls._collection_path(uid)}/{roadmap_id}"
        return await FirestoreClient.get_document(path)

    @classmethod
    async def save_roadmap(cls, uid: str, roadmap_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update roadmap."""
        path = f"{cls._collection_path(uid)}/{roadmap_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = roadmap_id
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def toggle_task(cls, uid: str, roadmap_id: str, task_id: str) -> Dict[str, Any]:
        """Toggle completion of a task within roadmap phases."""
        roadmap = await cls.get_roadmap(uid, roadmap_id)
        if not roadmap:
            return {}

        completed_tasks = set(roadmap.get("completed_task_ids", []))
        if task_id in completed_tasks:
            completed_tasks.remove(task_id)
        else:
            completed_tasks.add(task_id)

        # Recalculate progress percentage
        phases = roadmap.get("phases", [])
        total_tasks = 0
        for p in phases:
            total_tasks += len(p.get("tasks", []))

        progress = int((len(completed_tasks) / total_tasks * 100)) if total_tasks > 0 else 0
        progress = min(100, max(0, progress))

        update_payload = {
            "completed_task_ids": list(completed_tasks),
            "overall_progress_percent": progress,
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        return await cls.save_roadmap(uid, roadmap_id, update_payload)

    @classmethod
    async def toggle_milestone(cls, uid: str, roadmap_id: str, milestone_id: str) -> Dict[str, Any]:
        """Toggle completion of a milestone within roadmap."""
        roadmap = await cls.get_roadmap(uid, roadmap_id)
        if not roadmap:
            return {}

        completed = set(roadmap.get("completed_milestone_ids", []))
        if milestone_id in completed:
            completed.remove(milestone_id)
        else:
            completed.add(milestone_id)

        update_payload = {
            "completed_milestone_ids": list(completed),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        return await cls.save_roadmap(uid, roadmap_id, update_payload)

    @classmethod
    async def list_roadmaps(cls, uid: str) -> List[Dict[str, Any]]:
        """List all roadmaps for user."""
        return await FirestoreClient.query_collection(
            cls._collection_path(uid),
            order_by="created_at",
            descending=True
        )
