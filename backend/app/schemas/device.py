import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_enabled: bool | None = None


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    hostname: str | None
    os_name: str | None
    os_version: str | None
    architecture: str | None
    cpu_model: str | None
    cpu_physical_cores: int | None
    cpu_logical_cores: int | None
    memory_total_bytes: int | None
    agent_version: str | None
    last_seen_at: datetime | None
    is_enabled: bool
    created_at: datetime
    maintenance_until: datetime | None = None
    cpu_percent: float | None = None
    memory_percent: float | None = None
    root_disk_percent: float | None = None
    net_tx_bytes_per_sec: int | None = None
    net_rx_bytes_per_sec: int | None = None
    status: str = "offline"

    model_config = {"from_attributes": True}


class DeviceListResponse(BaseModel):
    items: list[DeviceResponse]
    page: int
    page_size: int
    total: int


class DashboardResponse(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    firing_alerts: int = 0
    alert_devices: int = 0
    top_cpu: list[DeviceResponse]
    top_memory: list[DeviceResponse]


class TokenResponse(BaseModel):
    token: str
    token_id: uuid.UUID
    token_prefix: str
    warning: str = "请立即复制保存，此 Token 之后无法再次查看"


class BootstrapRequest(BaseModel):
    agent_instance_id: uuid.UUID
    agent_version: str = Field(max_length=32)
    hostname: str = Field(min_length=1, max_length=255)


class BootstrapResponse(BaseModel):
    device_id: uuid.UUID
    collect_interval_seconds: int
    max_batch_samples: int
    server_time: datetime


class SystemInfoRequest(BaseModel):
    agent_instance_id: uuid.UUID
    hostname: str = Field(min_length=1, max_length=255)
    os_name: str = Field(max_length=64)
    os_version: str = Field(max_length=255)
    architecture: str = Field(max_length=64)
    cpu_model: str | None = Field(default=None, max_length=255)
    cpu_physical_cores: int | None = Field(default=None, ge=1)
    cpu_logical_cores: int | None = Field(default=None, ge=1)
    memory_total_bytes: int | None = Field(default=None, ge=0)
    agent_version: str = Field(max_length=32)


class SystemInfoResponse(BaseModel):
    device_id: uuid.UUID
    updated: bool = True
    server_time: datetime
