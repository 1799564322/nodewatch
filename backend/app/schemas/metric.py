import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DiskMetric(BaseModel):
    mountpoint: str = Field(min_length=1, max_length=255)
    filesystem: str | None = Field(default=None, max_length=64)
    total_bytes: int = Field(ge=0)
    used_bytes: int = Field(ge=0)
    percent: float = Field(ge=0, le=100)


class MetricRequest(BaseModel):
    sample_id: uuid.UUID
    collected_at: datetime
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    memory_used_bytes: int = Field(ge=0)
    swap_percent: float | None = Field(default=None, ge=0, le=100)
    root_disk_percent: float | None = Field(default=None, ge=0, le=100)
    root_disk_used_bytes: int | None = Field(default=None, ge=0)
    net_tx_bytes_per_sec: int = Field(ge=0)
    net_rx_bytes_per_sec: int = Field(ge=0)
    uptime_seconds: int = Field(ge=0)
    disks: list[DiskMetric] = Field(default_factory=list, max_length=100)


class MetricIngestResponse(BaseModel):
    accepted: int
    duplicate: int
    server_time: datetime


class MetricBatchRequest(BaseModel):
    samples: list[MetricRequest] = Field(min_length=1, max_length=500)


class HistoryPoint(BaseModel):
    collected_at: datetime
    cpu_percent: float
    memory_percent: float
    root_disk_percent: float | None
    net_tx_bytes_per_sec: int
    net_rx_bytes_per_sec: int


class HistoryResponse(BaseModel):
    resolution: str
    points: list[HistoryPoint]


class DiskResponse(DiskMetric):
    collected_at: datetime
