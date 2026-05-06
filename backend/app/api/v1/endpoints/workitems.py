import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mongodb import get_mongo_db
from app.db.postgres import get_db
from app.db.redis_client import get_redis
from app.models.workitem import WorkItem, WorkItemStatus
from app.schemas.workitem import (
    WorkItemDetailResponse,
    WorkItemResponse,
    StatusTransitionRequest,
)
from app.services.state_machine import get_state
from app.core.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}


@router.get("", response_model=list[WorkItemResponse])
async def list_workitems(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all work items sorted by severity (P0 first).
    Tries Redis cache first. Falls back to Postgres on cache miss.
    Cache is invalidated whenever a WorkItem is created or its status changes.
    """
    redis = await get_redis()
    cached = await redis.get("dashboard:workitems")
    if cached:
        raw = json.loads(cached)
        return [WorkItemResponse(**item) for item in raw]

    result = await db.execute(
        select(WorkItem).where(WorkItem.status != WorkItemStatus.CLOSED)
    )
    items = result.scalars().all()
    items.sort(key=lambda w: PRIORITY_ORDER.get(w.priority.value, 9))

    serialized = [WorkItemResponse.model_validate(i).model_dump(mode="json") for i in items]
    await redis.setex("dashboard:workitems", 30, json.dumps(serialized))

    return [WorkItemResponse.model_validate(i) for i in items]


@router.get("/{workitem_id}", response_model=WorkItemDetailResponse)
async def get_workitem(
    workitem_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Returns a single WorkItem with its linked raw signals from MongoDB
    and its RCA (if submitted).
    """
    wi = await db.get(WorkItem, workitem_id)
    if not wi:
        raise HTTPException(status_code=404, detail=f"WorkItem {workitem_id} not found")

    # Fetch raw signals from MongoDB
    mongo_db = get_mongo_db()
    cursor = mongo_db[settings.mongodb_signals_collection].find(
        {"workitem_id": workitem_id},
        {"_id": 0},
    ).sort("received_at", -1).limit(100)
    signals = await cursor.to_list(length=100)

    # Fetch RCA from Postgres if it exists
    from app.models.rca import RCA
    from sqlalchemy import select as sa_select
    rca_result = await db.execute(
        sa_select(RCA).where(RCA.workitem_id == workitem_id)
    )
    rca = rca_result.scalar_one_or_none()

    from app.schemas.rca import RCAResponse
    response = WorkItemDetailResponse.model_validate(wi)
    response.signals = signals
    response.rca = RCAResponse.model_validate(rca) if rca else None

    return response


@router.patch("/{workitem_id}/status", response_model=WorkItemResponse)
async def update_workitem_status(
    workitem_id: str,
    body: StatusTransitionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Transition a WorkItem through the state machine.
    Guards:
    - Invalid transitions are rejected with 422
    - Transitioning to CLOSED without an RCA is rejected with 422
    - CLOSED is a terminal state — no further transitions allowed
    """
    wi = await db.get(WorkItem, workitem_id)
    if not wi:
        raise HTTPException(status_code=404, detail=f"WorkItem {workitem_id} not found")

    # Check if RCA exists when targeting CLOSED
    rca_exists = False
    if body.status == WorkItemStatus.CLOSED:
        from app.models.rca import RCA
        from sqlalchemy import select as sa_select
        rca_result = await db.execute(
            sa_select(RCA).where(RCA.workitem_id == workitem_id)
        )
        rca_exists = rca_result.scalar_one_or_none() is not None

    # Delegate transition validation to State Pattern
    current_state = get_state(wi.status)
    current_state.transition_to(body.status, rca_exists=rca_exists)

    # If CLOSED, calculate and save MTTR.
    #   MTTR = RCA submission time - first signal time.
    #
    # In this implementation, WorkItem.created_at represents the time the
    # first debounced signal created the WorkItem, and RCA.submitted_at is
    # generated when the RCA is submitted.
    if body.status == WorkItemStatus.CLOSED:
        from app.models.rca import RCA
        from sqlalchemy import select as sa_select

        rca_result = await db.execute(
            sa_select(RCA).where(RCA.workitem_id == workitem_id)
        )
        rca = rca_result.scalar_one_or_none()

        if rca:
            delta = rca.submitted_at - wi.created_at
            wi.mttr_minutes = round(delta.total_seconds() / 60, 2)

            

    wi.status = body.status
    wi.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(wi)

    # Invalidate dashboard cache
    redis = await get_redis()
    await redis.delete("dashboard:workitems")

    logger.info("WorkItem %s transitioned to %s", workitem_id, body.status.value)
    return WorkItemResponse.model_validate(wi)
