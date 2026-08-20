from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.job import Job, SavedJob, JobApplication, ApplicationStatusHistory
from app.models.profile import UserProfile
from app.schemas.health import APIResponse
from app.schemas.job import (
    JobSchema,
    JobSearchQuery,
    JobMatchAnalysisResponse,
    SavedJobResponse,
    JobApplicationCreateRequest,
    JobApplicationUpdateRequest,
    JobApplicationResponse,
    ApplicationHistoryResponse
)
from app.services.job.providers.catalog_provider import CatalogJobProvider
from app.services.job.matching_engine import JobMatchingEngine
from app.services.job.tracker_service import JobTrackerService

router = APIRouter()
catalog_provider = CatalogJobProvider()
matching_engine = JobMatchingEngine()
tracker_service = JobTrackerService()


async def _sync_catalog_jobs_to_db(db: AsyncSession):
    """Seed catalog reference jobs into database if jobs table is empty."""
    stmt = select(Job)
    res = await db.execute(stmt)
    existing_jobs = res.scalars().all()

    if not existing_jobs:
        raw_catalog = await catalog_provider.search_jobs(limit=50)
        for c in raw_catalog:
            job_obj = Job(
                provider_id=c["provider_id"],
                provider_name=c["provider_name"],
                title=c["title"],
                company=c["company"],
                location=c["location"],
                is_remote=c["is_remote"],
                employment_type=c["employment_type"],
                experience_level=c["experience_level"],
                description=c["description"],
                required_skills=c["required_skills"],
                preferred_skills=c["preferred_skills"],
                education_requirements=c["education_requirements"],
                salary_min=c.get("salary_min"),
                salary_max=c.get("salary_max"),
                salary_currency=c.get("salary_currency", "USD"),
                source_url=c.get("source_url"),
                posted_date=c.get("posted_date")
            )
            db.add(job_obj)
        await db.commit()


@router.get(
    "/search",
    response_model=APIResponse[List[JobSchema]],
    summary="Search & filter jobs"
)
async def search_jobs(
    query: Optional[str] = Query(None, description="Search keyword, skill, or title"),
    location: Optional[str] = Query(None, description="Location search"),
    remote_only: Optional[bool] = Query(None, description="Filter remote only"),
    experience_level: Optional[str] = Query(None, description="Filter experience level"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    await _sync_catalog_jobs_to_db(db)

    # Fetch user saved job IDs & application statuses
    s_stmt = select(SavedJob.job_id).where(SavedJob.user_id == user_id)
    s_res = await db.execute(s_stmt)
    saved_ids = set(s_res.scalars().all())

    app_stmt = select(JobApplication).where(JobApplication.user_id == user_id)
    app_res = await db.execute(app_stmt)
    apps = {a.job_id: a.status for a in app_res.scalars().all()}

    stmt = select(Job)
    if query:
        q_like = f"%{query}%"
        stmt = stmt.where((Job.title.ilike(q_like)) | (Job.company.ilike(q_like)) | (Job.description.ilike(q_like)))

    if location:
        stmt = stmt.where(Job.location.ilike(f"%{location}%"))

    if remote_only is True:
        stmt = stmt.where(Job.is_remote == True)

    if experience_level:
        stmt = stmt.where(Job.experience_level.ilike(f"%{experience_level}%"))

    res = await db.execute(stmt)
    jobs = res.scalars().all()

    result_schemas = [
        JobSchema(
            id=j.id,
            provider_id=j.provider_id,
            provider_name=j.provider_name,
            title=j.title,
            company=j.company,
            location=j.location,
            is_remote=j.is_remote,
            employment_type=j.employment_type,
            experience_level=j.experience_level,
            description=j.description,
            required_skills=j.required_skills or [],
            preferred_skills=j.preferred_skills or [],
            education_requirements=j.education_requirements,
            salary_min=j.salary_min,
            salary_max=j.salary_max,
            salary_currency=j.salary_currency,
            source_url=j.source_url,
            posted_date=j.posted_date,
            is_saved=j.id in saved_ids,
            application_status=apps.get(j.id)
        )
        for j in jobs
    ]

    return APIResponse(
        success=True,
        message="Jobs retrieved successfully",
        data=result_schemas
    )


@router.get(
    "/recommended",
    response_model=APIResponse[List[JobMatchAnalysisResponse]],
    summary="Get top personalized job recommendations for current user profile"
)
async def get_recommended_jobs(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    await _sync_catalog_jobs_to_db(db)

    stmt = select(Job)
    res = await db.execute(stmt)
    all_jobs = res.scalars().all()

    matches: List[JobMatchAnalysisResponse] = []
    for j in all_jobs:
        analysis = await matching_engine.compute_job_match(db, user_id, j)
        matches.append(analysis)

    # Sort by overall match score descending
    matches.sort(key=lambda x: x.match_breakdown.overall_score, reverse=True)

    return APIResponse(
        success=True,
        message="Personalized job recommendations retrieved",
        data=matches[:10]
    )


@router.get(
    "/saved",
    response_model=APIResponse[List[SavedJobResponse]],
    summary="Get user bookmarked/saved jobs"
)
async def get_saved_jobs(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(SavedJob).options(selectinload(SavedJob.job)).where(SavedJob.user_id == user_id)
    res = await db.execute(stmt)
    saved_list = res.scalars().all()

    responses = []
    for sj in saved_list:
        j = sj.job
        if not j:
            continue
        job_schema = JobSchema(
            id=j.id,
            provider_id=j.provider_id,
            provider_name=j.provider_name,
            title=j.title,
            company=j.company,
            location=j.location,
            is_remote=j.is_remote,
            employment_type=j.employment_type,
            experience_level=j.experience_level,
            description=j.description,
            required_skills=j.required_skills or [],
            preferred_skills=j.preferred_skills or [],
            education_requirements=j.education_requirements,
            salary_min=j.salary_min,
            salary_max=j.salary_max,
            salary_currency=j.salary_currency,
            source_url=j.source_url,
            posted_date=j.posted_date,
            is_saved=True
        )
        responses.append(
            SavedJobResponse(
                id=sj.id,
                user_id=sj.user_id,
                job_id=sj.job_id,
                notes=sj.notes,
                saved_at=sj.saved_at.isoformat() if sj.saved_at else "",
                job=job_schema
            )
        )

    return APIResponse(
        success=True,
        message="Saved jobs retrieved successfully",
        data=responses
    )


@router.get(
    "/{job_id}",
    response_model=APIResponse[JobSchema],
    summary="Get specific job details"
)
async def get_job_details(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    j = res.scalars().first()

    if not j:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    s_stmt = select(SavedJob).where(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
    s_res = await db.execute(s_stmt)
    is_saved = bool(s_res.scalars().first())

    app_stmt = select(JobApplication).where(JobApplication.user_id == user_id, JobApplication.job_id == job_id)
    app_res = await db.execute(app_stmt)
    app_obj = app_res.scalars().first()

    schema = JobSchema(
        id=j.id,
        provider_id=j.provider_id,
        provider_name=j.provider_name,
        title=j.title,
        company=j.company,
        location=j.location,
        is_remote=j.is_remote,
        employment_type=j.employment_type,
        experience_level=j.experience_level,
        description=j.description,
        required_skills=j.required_skills or [],
        preferred_skills=j.preferred_skills or [],
        education_requirements=j.education_requirements,
        salary_min=j.salary_min,
        salary_max=j.salary_max,
        salary_currency=j.salary_currency,
        source_url=j.source_url,
        posted_date=j.posted_date,
        is_saved=is_saved,
        application_status=app_obj.status if app_obj else None
    )

    return APIResponse(
        success=True,
        message="Job details retrieved",
        data=schema
    )


@router.get(
    "/{job_id}/match",
    response_model=APIResponse[JobMatchAnalysisResponse],
    summary="Get detailed personalized match analysis & roadmap connections for a job"
)
async def get_job_match_analysis(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    j = res.scalars().first()

    if not j:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    analysis = await matching_engine.compute_job_match(db, user_id, j)
    return APIResponse(
        success=True,
        message="Job match analysis computed",
        data=analysis
    )


@router.post(
    "/{job_id}/save",
    response_model=APIResponse[SavedJobResponse],
    summary="Bookmark/Save a job"
)
async def save_job_endpoint(
    job_id: str,
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Job).where(Job.id == job_id)
    res = await db.execute(stmt)
    j = res.scalars().first()

    if not j:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    saved_obj = await tracker_service.save_job(db, user_id, job_id, notes)

    job_schema = JobSchema(
        id=j.id,
        title=j.title,
        company=j.company,
        location=j.location,
        is_remote=j.is_remote,
        employment_type=j.employment_type,
        experience_level=j.experience_level,
        description=j.description,
        required_skills=j.required_skills or [],
        preferred_skills=j.preferred_skills or [],
        education_requirements=j.education_requirements,
        salary_min=j.salary_min,
        salary_max=j.salary_max,
        salary_currency=j.salary_currency,
        is_saved=True
    )

    resp = SavedJobResponse(
        id=saved_obj.id,
        user_id=saved_obj.user_id,
        job_id=saved_obj.job_id,
        notes=saved_obj.notes,
        saved_at=saved_obj.saved_at.isoformat() if saved_obj.saved_at else "",
        job=job_schema
    )

    return APIResponse(
        success=True,
        message="Job saved successfully",
        data=resp
    )


@router.delete(
    "/{job_id}/save",
    response_model=APIResponse[bool],
    summary="Remove bookmarked job"
)
async def delete_saved_job_endpoint(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    success = await tracker_service.remove_saved_job(db, user_id, job_id)
    return APIResponse(
        success=success,
        message="Saved job removed" if success else "Saved job not found",
        data=success
    )


# ----------------------------------------------------
# Application Tracker Endpoints
# ----------------------------------------------------

@router.get(
    "/applications/all",
    response_model=APIResponse[List[JobApplicationResponse]],
    summary="Get all user job applications"
)
async def get_user_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(JobApplication).options(selectinload(JobApplication.job)).where(JobApplication.user_id == user_id)
    if status_filter:
        stmt = stmt.where(JobApplication.status.ilike(status_filter))

    res = await db.execute(stmt)
    apps = res.scalars().all()

    response_list = []
    for a in apps:
        j = a.job
        match_analysis = await matching_engine.compute_job_match(db, user_id, j) if j else None

        response_list.append(
            JobApplicationResponse(
                id=a.id,
                user_id=a.user_id,
                job_id=a.job_id,
                job_title=j.title if j else "Position",
                company=j.company if j else "Company",
                location=j.location if j else "Remote",
                status=a.status,
                applied_date=a.applied_date,
                interview_date=a.interview_date,
                notes=a.notes,
                source_url=a.source_url or (j.source_url if j else None),
                match_percentage=match_analysis.match_breakdown.overall_score if match_analysis else 75,
                readiness_status=match_analysis.match_breakdown.readiness_status if match_analysis else "NEARLY READY",
                created_at=a.created_at.isoformat() if a.created_at else "",
                updated_at=a.updated_at.isoformat() if a.updated_at else ""
            )
        )

    return APIResponse(
        success=True,
        message="Applications retrieved successfully",
        data=response_list
    )


@router.post(
    "/applications",
    response_model=APIResponse[JobApplicationResponse],
    summary="Create/Log a new job application"
)
async def create_job_application_endpoint(
    req: JobApplicationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(Job).where(Job.id == req.job_id)
    res = await db.execute(stmt)
    j = res.scalars().first()

    if not j:
        raise HTTPException(status_code=404, detail=f"Job '{req.job_id}' not found")

    app_obj = await tracker_service.create_application(
        db=db,
        user_id=user_id,
        job_id=req.job_id,
        status=req.status,
        applied_date=req.applied_date,
        interview_date=req.interview_date,
        notes=req.notes,
        source_url=req.source_url
    )

    match_analysis = await matching_engine.compute_job_match(db, user_id, j)

    resp = JobApplicationResponse(
        id=app_obj.id,
        user_id=app_obj.user_id,
        job_id=app_obj.job_id,
        job_title=j.title,
        company=j.company,
        location=j.location,
        status=app_obj.status,
        applied_date=app_obj.applied_date,
        interview_date=app_obj.interview_date,
        notes=app_obj.notes,
        source_url=app_obj.source_url or j.source_url,
        match_percentage=match_analysis.match_breakdown.overall_score,
        readiness_status=match_analysis.match_breakdown.readiness_status,
        created_at=app_obj.created_at.isoformat() if app_obj.created_at else "",
        updated_at=app_obj.updated_at.isoformat() if app_obj.updated_at else ""
    )

    return APIResponse(
        success=True,
        message="Application logged successfully",
        data=resp
    )


@router.put(
    "/applications/{application_id}",
    response_model=APIResponse[JobApplicationResponse],
    summary="Update application status, dates, or notes"
)
async def update_job_application_endpoint(
    application_id: str,
    req: JobApplicationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    try:
        app_obj, _ = await tracker_service.update_application_status(
            db=db,
            user_id=user_id,
            application_id=application_id,
            new_status=req.status,
            applied_date=req.applied_date,
            interview_date=req.interview_date,
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    j = app_obj.job
    match_analysis = await matching_engine.compute_job_match(db, user_id, j) if j else None

    resp = JobApplicationResponse(
        id=app_obj.id,
        user_id=app_obj.user_id,
        job_id=app_obj.job_id,
        job_title=j.title if j else "Position",
        company=j.company if j else "Company",
        location=j.location if j else "Remote",
        status=app_obj.status,
        applied_date=app_obj.applied_date,
        interview_date=app_obj.interview_date,
        notes=app_obj.notes,
        source_url=app_obj.source_url or (j.source_url if j else None),
        match_percentage=match_analysis.match_breakdown.overall_score if match_analysis else 75,
        readiness_status=match_analysis.match_breakdown.readiness_status if match_analysis else "NEARLY READY",
        created_at=app_obj.created_at.isoformat() if app_obj.created_at else "",
        updated_at=app_obj.updated_at.isoformat() if app_obj.updated_at else ""
    )

    return APIResponse(
        success=True,
        message="Application updated successfully",
        data=resp
    )


@router.delete(
    "/applications/{application_id}",
    response_model=APIResponse[bool],
    summary="Delete job application"
)
async def delete_job_application_endpoint(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    stmt = select(JobApplication).where(JobApplication.id == application_id, JobApplication.user_id == user_id)
    res = await db.execute(stmt)
    app_obj = res.scalars().first()

    if not app_obj:
        raise HTTPException(status_code=404, detail=f"Application '{application_id}' not found")

    await db.delete(app_obj)
    await db.commit()
    return APIResponse(
        success=True,
        message="Application deleted",
        data=True
    )


@router.get(
    "/applications/{application_id}/history",
    response_model=APIResponse[List[ApplicationHistoryResponse]],
    summary="Fetch status history audit trail for an application"
)
async def get_application_history(
    application_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    # Security check: verify application belongs to user
    stmt_app = select(JobApplication).where(JobApplication.id == application_id, JobApplication.user_id == user_id)
    res_app = await db.execute(stmt_app)
    app_obj = res_app.scalars().first()

    if not app_obj:
        raise HTTPException(status_code=404, detail=f"Application '{application_id}' not found for user")

    stmt_h = select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == application_id)
    res_h = await db.execute(stmt_h)
    history_entries = res_h.scalars().all()

    schema_list = [
        ApplicationHistoryResponse(
            id=h.id,
            application_id=h.application_id,
            from_status=h.from_status,
            to_status=h.to_status,
            changed_at=h.changed_at.isoformat() if h.changed_at else "",
            notes=h.notes
        )
        for h in history_entries
    ]

    return APIResponse(
        success=True,
        message="Application history retrieved",
        data=schema_list
    )
