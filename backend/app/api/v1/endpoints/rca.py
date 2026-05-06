import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.models.rca import RCA
from app.models.workitem import WorkItem, WorkItemStatus
from app.schemas.rca import RCACreate, RCAResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{workitem_id}/rca", response_model=RCAResponse, status_code=201)
async def submit_rca(
    workitem_id: str,
    body: RCACreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an RCA for a WorkItem.

    Rules:
    - WorkItem must exist
    - WorkItem must not be OPEN (must be at least INVESTIGATING)
    - RCA cannot be overwritten once submitted
    - All fields are validated by the RCACreate schema (times, category, min lengths)
    """
    wi = await db.get(WorkItem, workitem_id)
    if not wi:
        raise HTTPException(status_code=404, detail=f"WorkItem {workitem_id} not found")

    if wi.status == WorkItemStatus.OPEN:
        raise HTTPException(
            status_code=422,
            detail="Cannot submit RCA for an OPEN WorkItem. "
                   "Transition to INVESTIGATING first.",
        )

    if wi.status == WorkItemStatus.CLOSED:
        raise HTTPException(
            status_code=422,
            detail="Cannot submit RCA for a CLOSED WorkItem.",
        )

    # Check for duplicate RCA
    existing = await db.execute(
        select(RCA).where(RCA.workitem_id == workitem_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="RCA already submitted for this WorkItem. Cannot overwrite.",
        )

    rca = RCA(
        workitem_id=workitem_id,
        incident_start=body.incident_start,
        incident_end=body.incident_end,
        root_cause_category=body.root_cause_category,
        fix_applied=body.fix_applied,
        prevention_steps=body.prevention_steps,
    )
    db.add(rca)
    await db.commit()
    await db.refresh(rca)

    logger.info("RCA submitted for WorkItem %s [%s]", workitem_id, body.root_cause_category)
    return RCAResponse.model_validate(rca)


@router.get("/{workitem_id}/rca", response_model=RCAResponse)
async def get_rca(
    workitem_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the RCA for a given WorkItem."""
    wi = await db.get(WorkItem, workitem_id)
    if not wi:
        raise HTTPException(status_code=404, detail=f"WorkItem {workitem_id} not found")

    result = await db.execute(
        select(RCA).where(RCA.workitem_id == workitem_id)
    )
    rca = result.scalar_one_or_none()
    if not rca:
        raise HTTPException(
            status_code=404,
            detail=f"No RCA found for WorkItem {workitem_id}",
        )
    return RCAResponse.model_validate(rca)
