from pydantic import BaseModel
from datetime import datetime
from app.models.workitem import WorkItemStatus, Priority


class WorkItemResponse(BaseModel):
    id: str
    component_id: str
    status: WorkItemStatus
    priority: Priority
    alert_type: str
    signal_count: int
    created_at: datetime
    updated_at: datetime
    mttr_minutes: float | None = None

    class Config:
        from_attributes = True


class WorkItemDetailResponse(WorkItemResponse):
    """WorkItem with its linked signals from MongoDB."""
    signals: list[dict] = []
    rca: "RCAResponse | None" = None


class StatusTransitionRequest(BaseModel):
    status: WorkItemStatus


# avoid circular import
from app.schemas.rca import RCAResponse  # noqa: E402
WorkItemDetailResponse.model_rebuild()
