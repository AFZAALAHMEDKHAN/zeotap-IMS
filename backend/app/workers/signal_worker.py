import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.mongodb import get_mongo_db
from app.db.postgres import AsyncSessionLocal
from app.db.redis_client import get_redis
from app.models.workitem import WorkItem, WorkItemStatus
from app.services.alert_strategy import get_alert_strategy
from app.workers.queue import get_signal_queue

logger = logging.getLogger(__name__)
settings = get_settings()

# Metrics counter — reset every METRICS_INTERVAL_SECONDS
_signals_processed = 0


async def _get_or_create_workitem(
    component_id: str,
    priority: str,
    alert_type: str,
    redis,
) -> str:
    """
    Debounce logic using Redis TTL keys.

    Key: debounce:{component_id}
    Value: workitem_id
    TTL: DEBOUNCE_WINDOW_SECONDS

    If the key exists → link to existing WorkItem.
    If not → create a new WorkItem in Postgres and set the key.
    """
    debounce_key = f"debounce:{component_id}"
    existing_id = await redis.get(debounce_key)

    if existing_id:
        # Increment signal count on the existing WorkItem
        async with AsyncSessionLocal() as session:
            wi = await session.get(WorkItem, existing_id)
            if wi and wi.status not in (WorkItemStatus.CLOSED,):
                wi.signal_count += 1
                await session.commit()
        return existing_id

    # No active window — create a new WorkItem
    workitem_id = str(uuid.uuid4())
    async with AsyncSessionLocal() as session:
        wi = WorkItem(
            id=workitem_id,
            component_id=component_id,
            status=WorkItemStatus.OPEN,
            priority=priority,
            alert_type=alert_type,
            signal_count=1,
        )
        session.add(wi)
        await session.commit()

    # Set debounce key with TTL
    await redis.setex(
        debounce_key,
        settings.debounce_window_seconds,
        workitem_id,
    )

    # Invalidate dashboard cache so UI reflects new incident immediately
    await redis.delete("dashboard:workitems")

    logger.info(
        "New WorkItem created: %s for component %s [%s]",
        workitem_id, component_id, priority,
    )
    return workitem_id


async def _write_signal_to_mongo(signal: dict, workitem_id: str, retries: int = 0):
    """Write raw signal to MongoDB with exponential backoff retry."""
    try:
        db = get_mongo_db()
        signal["workitem_id"] = workitem_id
        await db[settings.mongodb_signals_collection].insert_one(signal)
    except Exception as exc:
        if retries < settings.db_write_max_retries:
            backoff = settings.db_write_retry_backoff * (2 ** retries)
            logger.warning(
                "MongoDB write failed (attempt %d/%d): %s. Retrying in %.1fs",
                retries + 1, settings.db_write_max_retries, exc, backoff,
            )
            await asyncio.sleep(backoff)
            await _write_signal_to_mongo(signal, workitem_id, retries + 1)
        else:
            logger.error("MongoDB write permanently failed after %d retries: %s", retries, exc)


async def _update_timeseries(component_id: str, severity: str):
    """Upsert a per-minute timeseries bucket in MongoDB."""
    try:
        db = get_mongo_db()
        now = datetime.now(timezone.utc)
        # Truncate to the current minute
        bucket = now.replace(second=0, microsecond=0)
        await db[settings.mongodb_timeseries_collection].update_one(
            {"timestamp": bucket, "component_id": component_id, "severity": severity},
            {"$inc": {"count": 1}},
            upsert=True,
        )
    except Exception as exc:
        logger.warning("Timeseries update failed: %s", exc)


async def process_signal(signal: dict):
    """
    Core processing pipeline for a single signal:
    1. Resolve alert strategy (Strategy Pattern)
    2. Debounce → get/create WorkItem (Redis + Postgres)
    3. Write raw signal to MongoDB with retry
    4. Update timeseries bucket
    """
    global _signals_processed
    _signals_processed += 1

    component_id = signal.get("component_id", "UNKNOWN")
    strategy = get_alert_strategy(component_id)
    priority = strategy.get_priority().value
    alert_type = strategy.get_alert_type()

    redis = await get_redis()

    try:
        workitem_id = await _get_or_create_workitem(
            component_id, priority, alert_type, redis
        )
    except Exception as exc:
        logger.error("Failed to get/create WorkItem for %s: %s", component_id, exc)
        return

    await _write_signal_to_mongo(signal, workitem_id)
    await _update_timeseries(component_id, signal.get("severity", "P1"))


async def signal_worker():
    """
    Long-running background task. Drains the asyncio.Queue continuously.
    Runs for the entire lifetime of the FastAPI process.
    """
    queue = get_signal_queue()
    logger.info("Signal worker started. Waiting for signals...")

    while True:
        try:
            signal = await queue.get()
            await process_signal(signal)
            queue.task_done()
        except asyncio.CancelledError:
            logger.info("Signal worker shutting down.")
            break
        except Exception as exc:
            logger.exception("Unhandled error in signal worker: %s", exc)
            # Don't crash the worker — log and continue
            await asyncio.sleep(0.1)


async def metrics_logger():
    """
    Background task: prints signals/sec to console every METRICS_INTERVAL_SECONDS.
    Also logs queue depth so ops can see backpressure building.
    """
    global _signals_processed
    interval = settings.metrics_interval_seconds

    while True:
        await asyncio.sleep(interval)
        queue = get_signal_queue()
        rate = _signals_processed / interval
        logger.info(
            "[METRICS] throughput=%.1f signals/sec | queue_depth=%d/%d",
            rate,
            queue.qsize(),
            settings.queue_max_size,
        )
        _signals_processed = 0
