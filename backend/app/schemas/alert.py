import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    device_id: uuid.UUID | None
    metric: str
    operator: str
    threshold: float | None
    duration_seconds: int
    severity: str
    is_enabled: bool
    model_config = {"from_attributes": True}

class AlertRuleUpdate(BaseModel):
    threshold: float | None = Field(default=None, ge=0)
    duration_seconds: int | None = Field(default=None, ge=0)
    severity: str | None = Field(default=None, pattern="^(info|warning|critical)$")
    is_enabled: bool | None = None

class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    device_id: uuid.UUID | None = None
    metric: str = Field(pattern="^(cpu|memory|root_disk|offline)$")
    operator: str = Field(default="gt", pattern="^(gt|gte|lt|lte)$")
    threshold: float | None = Field(default=None, ge=0)
    duration_seconds: int = Field(ge=0)
    severity: str = Field(pattern="^(info|warning|critical)$")

class AlertEventResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    rule_id: uuid.UUID
    status: str
    severity: str
    title: str
    message: str
    observed_value: float | None
    threshold_value: float | None
    started_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    model_config = {"from_attributes": True}

class MaintenanceRequest(BaseModel):
    until: datetime
