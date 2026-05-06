from fastapi import APIRouter
from app.api.v1.endpoints import signals, workitems, rca

api_router = APIRouter()

api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(workitems.router, prefix="/workitems", tags=["workitems"])
api_router.include_router(rca.router, prefix="/workitems", tags=["rca"])
