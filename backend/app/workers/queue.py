import asyncio
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Single shared queue instance for the process lifetime.
# maxsize enforces backpressure — if the queue is full, put_nowait raises
# QueueFull instead of growing unbounded and crashing the process.
_signal_queue: asyncio.Queue | None = None


def get_signal_queue() -> asyncio.Queue:
    global _signal_queue
    if _signal_queue is None:
        _signal_queue = asyncio.Queue(maxsize=settings.queue_max_size)
    return _signal_queue


async def enqueue_signal(signal: dict) -> int:
    """
    Drop a signal onto the queue. Returns current queue size.
    If queue is full, logs a warning and drops the signal (fail-open).
    This is intentional: we prefer dropping signals over crashing the
    ingestion endpoint under extreme load (backpressure strategy).

    await queue.put(signal)      # waits if queue is full — blocks until space available
    queue.put_nowait(signal)     # raises QueueFull immediately if queue is full
    """
    queue = get_signal_queue()
    try:
        queue.put_nowait(signal)
        return queue.qsize()
    except asyncio.QueueFull:
        logger.warning(
            "Signal queue full (%d/%d). Dropping signal for component: %s",
            queue.qsize(),
            settings.queue_max_size,
            signal.get("component_id", "unknown"),
        )
        return queue.qsize()
