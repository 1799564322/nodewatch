import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import signal
import threading
import time

from nodewatch_agent import __version__
from nodewatch_agent.cache import MetricCache
from nodewatch_agent.client import AgentClient, AgentRequestError
from nodewatch_agent.collector import MetricsCollector, collect_system_info
from nodewatch_agent.config import AgentConfig, load_config
from nodewatch_agent.identity import load_or_create_instance_id
from nodewatch_agent.retry import ExponentialBackoff


def configure_logging(config: AgentConfig, base_dir: Path) -> logging.Logger:
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    log_path = base_dir / "logs" / "agent.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rotating_file = RotatingFileHandler(
        log_path,
        maxBytes=config.log_max_bytes,
        backupCount=config.log_backup_count,
        encoding="utf-8",
    )
    rotating_file.setFormatter(formatter)
    logger = logging.getLogger("nodewatch_agent")
    logger.setLevel(config.log_level)
    logger.handlers.clear()
    logger.addHandler(console)
    logger.addHandler(rotating_file)
    logger.propagate = False
    return logger


def run(config_path: Path, once: bool = False) -> None:
    config_path = config_path.resolve()
    base_dir = config_path.parent
    config = load_config(config_path)
    logger = configure_logging(config, base_dir)
    stop_event = threading.Event()

    def request_stop(_signum=None, _frame=None) -> None:
        logger.info("收到退出信号，正在安全关闭")
        stop_event.set()

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    instance_id = load_or_create_instance_id(base_dir / "state" / "identity.json")
    cache = MetricCache(
        base_dir / "state" / "metrics.db",
        config.cache_max_samples,
        config.cache_retention_days,
    )
    client = AgentClient(config)
    collector = MetricsCollector()
    system_info = collect_system_info()
    backoff = ExponentialBackoff(config.retry_max_seconds)
    collect_interval = config.collect_interval_seconds
    batch_size = config.max_batch_samples
    bootstrapped = False
    next_collect_at = time.monotonic()
    next_upload_at = time.monotonic()
    collected_once = False

    try:
        while not stop_event.is_set():
            now = time.monotonic()
            if now >= next_collect_at:
                metric = collector.collect()
                cache.enqueue(metric)
                collected_once = True
                next_collect_at = now + collect_interval
                logger.info(
                    "指标已写入缓存 queued=%s CPU=%.1f%% 内存=%.1f%%",
                    cache.count(),
                    metric["cpu_percent"],
                    metric["memory_percent"],
                )

            if now >= next_upload_at:
                try:
                    if not bootstrapped:
                        bootstrap = client.bootstrap(instance_id, system_info)
                        client.send_system_info(instance_id, system_info)
                        collect_interval = bootstrap["collect_interval_seconds"]
                        batch_size = min(config.max_batch_samples, bootstrap["max_batch_samples"])
                        bootstrapped = True
                        logger.info(
                            "Agent 已绑定 device_id=%s token_prefix=%s",
                            bootstrap["device_id"],
                            config.agent_token[:12],
                        )
                    batch = cache.oldest(batch_size)
                    if batch:
                        result = client.send_metrics(batch)
                        cache.remove([str(metric["sample_id"]) for metric in batch])
                        logger.info(
                            "批量上报 accepted=%s duplicate=%s remaining=%s",
                            result["accepted"],
                            result["duplicate"],
                            cache.count(),
                        )
                    backoff.reset()
                    next_upload_at = time.monotonic() if cache.count() else next_collect_at
                except AgentRequestError as exc:
                    bootstrapped = False
                    if exc.authentication_error:
                        delay = config.retry_max_seconds
                        logger.error("%s；认证/绑定错误，%s 秒后重试", exc, delay)
                    elif exc.retryable:
                        delay = max(1.0, backoff.next_delay())
                        logger.warning("%s；%.1f 秒后重试", exc, delay)
                    else:
                        delay = config.retry_max_seconds
                        logger.error("%s；请求不可重试，%s 秒后再检查", exc, delay)
                    next_upload_at = time.monotonic() + delay

            if once and collected_once:
                return
            wake_at = min(next_collect_at, next_upload_at)
            stop_event.wait(max(0.1, wake_at - time.monotonic()))
    finally:
        client.close()
        cache.close()
        logger.info("Agent 已安全退出")


def main() -> None:
    parser = argparse.ArgumentParser(description="NodeWatch Agent")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    parser.add_argument("--once", action="store_true", help="完成一次采集和上报尝试后退出")
    args = parser.parse_args()
    run(args.config, args.once)


if __name__ == "__main__":
    main()
