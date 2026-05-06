from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class SignalIngestion(BaseModel):
    """Payload sent by external systems to report an error signal."""
    component_id: str = Field(..., min_length=1, max_length=100, examples=["CACHE_CLUSTER_01"])
    error_message: str = Field(..., min_length=1, max_length=2000)
    severity: str = Field(..., pattern="^(P0|P1|P2)$", examples=["P0"])
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class SignalResponse(BaseModel):
    """Returned immediately after signal ingestion — before async processing."""
    status: str = "accepted"
    message: str = "Signal queued for processing"
    queue_size: int


class SignalDetail(BaseModel):
    """Full signal document as stored in MongoDB."""
    id: str
    workitem_id: str | None
    component_id: str
    error_message: str
    severity: str
    raw_payload: dict[str, Any]
    received_at: datetime

    class Config:
        from_attributes = True
