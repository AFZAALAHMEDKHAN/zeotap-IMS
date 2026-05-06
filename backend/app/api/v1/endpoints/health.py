from fastapi import APIRouter
from sqlalchemy import text
from app.db.postgres import AsyncSessionLocal
from app.db.mongodb import get_mongo_db
from app.db.redis_client import get_redis
from app.core.config import get_settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/health")
async def health_check():
    """
    Checks connectivity to all three backing stores individually.
    Returns per-service status so you can see exactly which component
    is degraded rather than a generic pass/fail.
    """
    status = {"postgres": "ok", "mongodb": "ok", "redis": "ok", "overall": "ok"}

    # Postgres
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        status["postgres"] = f"error: {exc}"
        status["overall"] = "degraded"

    # MongoDB
    try:
        db = get_mongo_db()
        await db.command("ping")
    except Exception as exc:
        status["mongodb"] = f"error: {exc}"
        status["overall"] = "degraded"

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
    except Exception as exc:
        status["redis"] = f"error: {exc}"
        status["overall"] = "degraded"

    return status


@router.get("/api/v1/metrics/timeseries")
async def get_timeseries():
    """
    Returns signals per minute over the last 60 minutes.
    Sourced from the timeseries collection in MongoDB.
    """
    from datetime import datetime, timezone, timedelta
    db = get_mongo_db()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)

    cursor = db[settings.mongodb_timeseries_collection].find(
        {"timestamp": {"$gte": cutoff}},
        {"_id": 0},
    ).sort("timestamp", 1)

    results = await cursor.to_list(length=500)
    for r in results:
        if hasattr(r.get("timestamp"), "isoformat"):
            r["timestamp"] = r["timestamp"].isoformat()

    return {"data": results}
