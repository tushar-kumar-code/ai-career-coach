import uuid
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.job import Job, SavedJob, JobApplication, ApplicationStatusHistory
from app.schemas.job import JobApplicationResponse, ApplicationHistoryResponse, SavedJobResponse

logger = logging.getLogger(__name__)


class JobTrackerService:
    """Service managing bookmarked jobs, application lifecycle transitions, and audit status history."""

    async def save_job(self, db: AsyncSession, user_id: str, job_id: str, notes: Optional[str] = None) -> SavedJob:
        """Bookmark a job for a user."""
        stmt = select(SavedJob).where(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        res = await db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            if notes is not None:
                existing.notes = notes
                await db.commit()
                await db.refresh(existing)
            return existing

        new_saved = SavedJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            job_id=job_id,
            notes=notes,
            saved_at=datetime.utcnow()
        )
        db.add(new_saved)
        await db.commit()
        await db.refresh(new_saved)
        return new_saved

    async def remove_saved_job(self, db: AsyncSession, user_id: str, job_id: str) -> bool:
        """Remove a bookmarked job."""
        stmt = select(SavedJob).where(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        res = await db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            await db.delete(existing)
            await db.commit()
            return True
        return False

    async def create_application(
        self,
        db: AsyncSession,
        user_id: str,
        job_id: str,
        status: str = "Applied",
        applied_date: Optional[str] = None,
        interview_date: Optional[str] = None,
        notes: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> JobApplication:
        """Log a new job application and initialize status audit log."""
        today_str = applied_date or datetime.utcnow().strftime("%Y-%m-%d")

        stmt = select(JobApplication).where(JobApplication.user_id == user_id, JobApplication.job_id == job_id)
        res = await db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            old_status = existing.status
            existing.status = status
            if applied_date:
                existing.applied_date = applied_date
            if interview_date:
                existing.interview_date = interview_date
            if notes is not None:
                existing.notes = notes
            if source_url:
                existing.source_url = source_url

            # Audit history if status changed
            if old_status != status:
                history_entry = ApplicationStatusHistory(
                    id=str(uuid.uuid4()),
                    application_id=existing.id,
                    from_status=old_status,
                    to_status=status,
                    notes=notes or f"Updated status to {status}"
                )
                db.add(history_entry)

            await db.commit()
            await db.refresh(existing)
            return existing

        new_app = JobApplication(
            id=str(uuid.uuid4()),
            user_id=user_id,
            job_id=job_id,
            status=status,
            applied_date=today_str,
            interview_date=interview_date,
            notes=notes,
            source_url=source_url
        )
        db.add(new_app)
        await db.flush()

        history_entry = ApplicationStatusHistory(
            id=str(uuid.uuid4()),
            application_id=new_app.id,
            from_status=None,
            to_status=status,
            notes="Application record initialized"
        )
        db.add(history_entry)

        await db.commit()
        await db.refresh(new_app)
        return new_app

    async def update_application_status(
        self,
        db: AsyncSession,
        user_id: str,
        application_id: str,
        new_status: Optional[str] = None,
        applied_date: Optional[str] = None,
        interview_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[JobApplication, bool]:
        """Update job application status & record audit history entry."""
        stmt = select(JobApplication).options(selectinload(JobApplication.job)).where(JobApplication.id == application_id, JobApplication.user_id == user_id)
        res = await db.execute(stmt)
        app_obj = res.scalars().first()

        if not app_obj:
            raise ValueError(f"Job application '{application_id}' not found for user")

        old_status = app_obj.status
        status_changed = False

        if new_status and new_status != old_status:
            app_obj.status = new_status
            status_changed = True

            history_entry = ApplicationStatusHistory(
                id=str(uuid.uuid4()),
                application_id=app_obj.id,
                from_status=old_status,
                to_status=new_status,
                notes=notes or f"Transitioned status from {old_status} to {new_status}"
            )
            db.add(history_entry)

        if applied_date:
            app_obj.applied_date = applied_date
        if interview_date:
            app_obj.interview_date = interview_date
        if notes is not None:
            app_obj.notes = notes

        await db.commit()
        await db.refresh(app_obj)
        return app_obj, status_changed
