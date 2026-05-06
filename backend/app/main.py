import asyncio
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.api.v1.endpoints.health import router as health_router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.postgres import init_db
from app.db.mongodb import init_mongo, close_mongo
from app.db.redis_client import get_redis, close_redis
from app.workers.signal_worker import signal_worker, metrics_logger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


app = FastAPI(
    title="Incident Management System",
    description="Mission-critical IMS for distributed infrastructure monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — origins are env-driven via CORS_ALLOWED_ORIGINS (comma-separated)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router)


@app.on_event("startup")
async def startup():
    logger.info("Starting IMS backend...")

    # Initialize databases
    await init_db()
    logger.info("PostgreSQL tables created/verified")

    await init_mongo()
    logger.info("MongoDB indexes created/verified")

    await get_redis()
    logger.info("Redis connection established")

    # Start background workers as asyncio tasks
    asyncio.create_task(signal_worker(), name="signal_worker")
    asyncio.create_task(metrics_logger(), name="metrics_logger")
    logger.info("Background workers started")

    logger.info("IMS backend ready on http://0.0.0.0:8000")
    logger.info("API docs at http://0.0.0.0:8000/docs")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down IMS backend...")

    # Cancel background tasks gracefully
    for task in asyncio.all_tasks():
        if task.get_name() in ("signal_worker", "metrics_logger"):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    await close_mongo()
    await close_redis()
    logger.info("IMS backend stopped cleanly")
