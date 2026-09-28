import datetime
from typing import Optional, Dict, Any, List
from app.services.firestore.client import FirestoreClient


class DigitalTwinRepository:
    """Manages Career Digital Twin, readiness snapshots, user achievements, and weekly reports in Firestore."""

    @staticmethod
    def _twin_path(uid: str) -> str:
        return f"users/{uid}/digital_twin/current"

    @staticmethod
    def _snapshots_path(uid: str) -> str:
        return f"users/{uid}/readiness_snapshots"

    @staticmethod
    def _achievements_path(uid: str) -> str:
        return f"users/{uid}/achievements"

    @staticmethod
    def _reports_path(uid: str) -> str:
        return f"users/{uid}/weekly_reports"

    # --- Digital Twin Core ---

    @classmethod
    async def get_digital_twin(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch current live Digital Twin state."""
        return await FirestoreClient.get_document(cls._twin_path(uid))

    @classmethod
    async def save_digital_twin(cls, uid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update live Digital Twin state."""
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["updated_at"] = now
        if "created_at" not in payload:
            payload["created_at"] = now
        return await FirestoreClient.set_document(cls._twin_path(uid), payload, merge=True)

    # --- Historical Readiness Snapshots ---

    @classmethod
    async def save_snapshot(cls, uid: str, snapshot_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a daily score snapshot for historical trends."""
        path = f"{cls._snapshots_path(uid)}/{snapshot_id}"
        payload = dict(data)
        now = datetime.datetime.utcnow().isoformat()
        payload["uid"] = uid
        payload["id"] = snapshot_id
        payload["created_at"] = payload.get("created_at") or now
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def list_snapshots(cls, uid: str, limit: int = 30) -> List[Dict[str, Any]]:
        """List historical readiness snapshots ordered chronologically."""
        return await FirestoreClient.query_collection(
            cls._snapshots_path(uid),
            order_by="snapshot_date",
            descending=False,
            limit=limit
        )

    # --- Earned Achievements ---

    @classmethod
    async def save_achievement(cls, uid: str, achievement_key: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record an earned achievement."""
        path = f"{cls._achievements_path(uid)}/{achievement_key}"
        payload = dict(data)
        payload["uid"] = uid
        payload["achievement_key"] = achievement_key
        if "earned_at" not in payload:
            payload["earned_at"] = datetime.datetime.utcnow().isoformat()
        return await FirestoreClient.set_document(path, payload, merge=True)

    @classmethod
    async def save_achievements(cls, uid: str, achievements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Batch save multiple achievements for user."""
        saved = []
        for ach in achievements:
            key = ach.get("achievement_key") or ach.get("id") or str(ach.get("title", "ach")).lower().replace(" ", "_")
            saved.append(await cls.save_achievement(uid, key, ach))
        return saved

    @classmethod
    async def list_achievements(cls, uid: str) -> List[Dict[str, Any]]:
        """List all earned achievements for user."""
        return await FirestoreClient.query_collection(
            cls._achievements_path(uid),
            order_by="earned_at",
            descending=True
        )

    # --- Weekly Career Reports ---

    @classmethod
    async def save_weekly_report(cls, uid: str, report_or_id: Any, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Save a generated weekly career progress report (supports both (uid, data) and (uid, report_id, data))."""
        if data is None and isinstance(report_or_id, dict):
            report_data = dict(report_or_id)
            report_id = report_data.get("id") or report_data.get("report_id") or f"week_{datetime.date.today().isoformat()}"
        else:
            report_id = str(report_or_id)
            report_data = dict(data or {})

        path = f"{cls._reports_path(uid)}/{report_id}"
        now = datetime.datetime.utcnow().isoformat()
        report_data["uid"] = uid
        report_data["id"] = report_id
        report_data["generated_at"] = report_data.get("generated_at") or now
        return await FirestoreClient.set_document(path, report_data, merge=True)

    @classmethod
    async def get_latest_weekly_report(cls, uid: str) -> Optional[Dict[str, Any]]:
        """Fetch latest weekly report."""
        docs = await FirestoreClient.query_collection(
            cls._reports_path(uid),
            order_by="generated_at",
            descending=True,
            limit=1
        )
        return docs[0] if docs else None
