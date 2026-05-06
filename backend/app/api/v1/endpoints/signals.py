from fastapi import APIRouter, Request
from datetime import datetime, timezone
import uuid

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.signal import SignalIngestion, SignalResponse
from app.workers.queue import enqueue_signal

router = APIRouter()
settings = get_settings()

@router.post("", response_model=SignalResponse, status_code=202)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def ingest_signal(request: Request, payload: SignalIngestion):
    """
    High-throughput signal ingestion endpoint.

    Immediately drops the signal into the in-memory asyncio.Queue
    and returns 202 Accepted. No DB writes happen in this path —
    that keeps latency under 1ms even under heavy load.

    Rate limited by SlowAPI using the shared limiter configured in main.py.
    """
    signal = {
        "_id": str(uuid.uuid4()),
        "component_id": payload.component_id,
        "error_message": payload.error_message,
        "severity": payload.severity,
        "raw_payload": payload.raw_payload,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    queue_size = await enqueue_signal(signal)

    return SignalResponse(
        status="accepted",
        message="Signal queued for processing",
        queue_size=queue_size,
    )
