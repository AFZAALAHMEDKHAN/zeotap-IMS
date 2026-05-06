from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings

settings = get_settings()

_client: AsyncIOMotorClient | None = None   


def get_mongo_client() -> AsyncIOMotorClient:
    global _client # so that we are modifying the global variable, not creating a local one
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    return get_mongo_client()[settings.mongodb_db_name]


async def init_mongo():
    """Create indexes for efficient querying."""
    db = get_mongo_db()

    # Index on workitem_id for fast signal lookup per incident
    await db[settings.mongodb_signals_collection].create_index("workitem_id")
    # Index on component_id + received_at for debounce queries
    await db[settings.mongodb_signals_collection].create_index(
        [("component_id", 1), ("received_at", -1)]
    )
    # TTL index on timeseries — auto-delete records older than 7 days
    await db[settings.mongodb_timeseries_collection].create_index(
        "timestamp", expireAfterSeconds=604800
    )


async def close_mongo():
    global _client
    if _client:
        _client.close()
        _client = None
