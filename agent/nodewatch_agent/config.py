from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class AgentConfig:
    server_url: str
    agent_token: str
    collect_interval_seconds: int = 60
    request_timeout_seconds: int = 10
    verify_tls: bool = True
    log_level: str = "INFO"
    cache_max_samples: int = 10000
    cache_retention_days: int = 7
    max_batch_samples: int = 500
    retry_max_seconds: int = 300
    log_max_bytes: int = 5_242_880
    log_backup_count: int = 3


def load_config(path: Path) -> AgentConfig:
    with path.open("rb") as config_file:
        values = tomllib.load(config_file)
    config = AgentConfig(**values)
    if not config.agent_token.startswith("nwa_"):
        raise ValueError("agent_token 格式无效")
    if config.collect_interval_seconds < 10:
        raise ValueError("collect_interval_seconds 不能小于 10")
    if not 1 <= config.max_batch_samples <= 500:
        raise ValueError("max_batch_samples 必须在 1 到 500 之间")
    if config.cache_max_samples < config.max_batch_samples:
        raise ValueError("cache_max_samples 不能小于 max_batch_samples")
    return config
