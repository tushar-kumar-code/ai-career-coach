import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class JobsRepository:
    """Manages user saved jobs and job applications in Firestore under users/{uid}/..."""

    @staticmethod
    def _saved_jobs_path(uid: str) -> str:
        return f"users/{uid}/saved_jobs"

    @staticmethod
    def _applications_path(uid: str) -> str:
        return f"users/{uid}/job_applications"

    # --- Saved Jobs ---

    @classmethod
    async def get_saved_jobs(cls, uid: str) -> List[Dict[str, Any]]:
        """List all saved jobs for user."""
        return await FirestoreClient.query_collection(
            cls._saved_jobs_path(uid),
            order_by="saved_at",
            descending=True
        )

    @classmethod
    async def save_job(cls, uid: str, job_id: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save a job posting to user's saved list."""
        path = f"{cls._saved_jobs_path(uid)}/{job_id}"
        payload = dict(data or {})
        payload["uid"] = uid
        payload["job_id"] = job_id
        if "saved_at" not in payload:
            payload["saved_at"] = datetime.datetime.utcnow().isoformat()
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def unsave_job(cls, uid: str, job_id: str) -> bool:
        """Remove a job from user's saved list."""
        path = f"{cls._saved_jobs_path(uid)}/{job_id}"
        return await FirestoreClient.delete_document(path)

    @classmethod
    async def is_job_saved(cls, uid: str, job_id: str) -> bool:
        """Check if job is saved by user."""
        path = f"{cls._saved_jobs_path(uid)}/{job_id}"
        doc = await FirestoreClient.get_document(path)
        return doc is not None

    # --- Job Applications ---

    @classmethod
    async def get_applications(cls, uid: str) -> List[Dict[str, Any]]:
        """List user's tracked job applications."""
        return await FirestoreClient.query_collection(
            cls._applications_path(uid),
            order_by="applied_date",
            descending=True
        )

    @classmethod
    async def get_application(cls, uid: str, app_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a specific job application."""
        path = f"{cls._applications_path(uid)}/{app_id}"
        return await FirestoreClient.get_document(path)

    @classmethod
    async def save_application(cls, uid: str, app_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new job application."""
        path = f"{cls._applications_path(uid)}/{app_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = app_id
        payload["updated_at"] = now
        if "applied_date" not in payload:
            payload["applied_date"] = now
        if "status_history" not in payload:
            payload["status_history"] = [{
                "status": payload.get("status", "APPLIED"),
                "notes": payload.get("notes", "Application submitted"),
                "changed_at": now
            }]
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def update_application_status(
        cls,
        uid: str,
        app_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update status of a job application and log history."""
        app = await cls.get_application(uid, app_id)
        if not app:
            return {}

        now = datetime.datetime.utcnow().isoformat()
        history = list(app.get("status_history", []))
        history.append({
            "status": status,
            "notes": notes or "",
            "changed_at": now
        })

        update_payload = {
            "status": status,
            "status_history": history,
            "updated_at": now
        }
        return await cls.save_application(uid, app_id, update_payload)
