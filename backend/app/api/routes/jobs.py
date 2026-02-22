"""Job trigger and status API."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.organization import Organization, Property
from app.models.user import User
from app.models.job import BackgroundJob
from app.services.org_access import user_has_property_access
from app.tasks.engine import run_engine_a, run_engine_b
from app.tasks.training import run_training_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


class TriggerEngineRequest(BaseModel):
    property_id: str


@router.post("/engine-a")
async def trigger_engine_a(
    body: TriggerEngineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger Engine A (tactical 0-30 days) run."""
    property_id = body.property_id
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    task = run_engine_a.delay(property_id)
    job = BackgroundJob(
        id=str(uuid.uuid4()),
        job_type="engine_a",
        celery_task_id=task.id,
        status="pending",
        property_id=property_id,
        payload={"property_id": property_id},
    )
    db.add(job)
    await db.flush()
    return {
        "job_id": job.id,
        "celery_task_id": task.id,
        "status": "pending",
        "message": "Engine A run started",
    }


@router.post("/engine-b")
async def trigger_engine_b(
    body: TriggerEngineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger Engine B (strategic 31-365 days) run."""
    property_id = body.property_id
    if not await user_has_property_access(db, current_user.id, property_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    task = run_engine_b.delay(property_id)
    job = BackgroundJob(
        id=str(uuid.uuid4()),
        job_type="engine_b",
        celery_task_id=task.id,
        status="pending",
        property_id=property_id,
        payload={"property_id": property_id},
    )
    db.add(job)
    await db.flush()
    return {
        "job_id": job.id,
        "celery_task_id": task.id,
        "status": "pending",
        "message": "Engine B run started",
    }


@router.get("/status/{job_id}")
async def job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get job status - poll for progress."""
    from celery.result import AsyncResult
    from app.celery_app import celery_app

    result = await db.execute(
        select(BackgroundJob)
        .join(Property, BackgroundJob.property_id == Property.id)
        .join(Organization, Property.organization_id == Organization.id)
        .where(
            BackgroundJob.id == job_id,
            Organization.owner_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.celery_task_id:
        async_result = AsyncResult(job.celery_task_id, app=celery_app)
        state = async_result.state
        info = async_result.info or {}
        if state == "SUCCESS":
            from datetime import datetime, timezone
            from sqlalchemy import update
            job.result = async_result.result
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
            return {"job_id": job_id, "status": "completed", "result": async_result.result}
        if state == "FAILURE":
            from datetime import datetime, timezone
            job.error = str(async_result.result)
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
            return {"job_id": job_id, "status": "failed", "error": str(async_result.result)}
        if state == "PROGRESS":
            return {"job_id": job_id, "status": "running", "progress": info}

    return {"job_id": job_id, "status": job.status}


@router.post("/training")
async def trigger_training(
    body: TriggerEngineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger training job for property - builds dataset, trains, registers model."""
    if not await user_has_property_access(db, current_user.id, body.property_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found",
        )

    task = run_training_job.delay(body.property_id)
    job = BackgroundJob(
        id=str(uuid.uuid4()),
        job_type="training",
        celery_task_id=task.id,
        status="pending",
        property_id=body.property_id,
        payload={"property_id": body.property_id},
    )
    db.add(job)
    await db.flush()
    return {
        "job_id": job.id,
        "celery_task_id": task.id,
        "status": "pending",
        "message": "Training job started",
    }
