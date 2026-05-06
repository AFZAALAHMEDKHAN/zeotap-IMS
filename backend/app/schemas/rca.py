from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from app.models.rca import VALID_CATEGORIES


class RCACreate(BaseModel):
    incident_start: datetime
    incident_end: datetime
    root_cause_category: str = Field(..., examples=["DATABASE_FAILURE"])
    fix_applied: str = Field(..., min_length=10, max_length=5000)
    prevention_steps: str = Field(..., min_length=10, max_length=5000)

    @model_validator(mode="after")
    def validate_times_and_category(self) -> "RCACreate":
        if self.incident_end <= self.incident_start:
            raise ValueError("incident_end must be after incident_start")
        if self.root_cause_category not in VALID_CATEGORIES:
            raise ValueError(
                f"root_cause_category must be one of: {', '.join(VALID_CATEGORIES)}"
            )
        return self


class RCAResponse(BaseModel):
    id: str
    workitem_id: str
    incident_start: datetime
    incident_end: datetime
    root_cause_category: str
    fix_applied: str
    prevention_steps: str
    submitted_at: datetime

    class Config:
        from_attributes = True
