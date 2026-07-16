import logging
import os
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import delete

from app.core.config import get_settings
from app.db.session import session_scope
from app.models.metric import MetricSample
from app.models.user_session import UserSession
from app.services.alerts import evaluate_offline_devices

logger = logging.getLogger(__name__)


def check_offline() -> None:
    with session_scope() as session:
        evaluate_offline_devices(session)


def cleanup_expired_data() -> None:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=get_settings().raw_metric_retention_days)
    with session_scope() as session:
        session.execute(delete(UserSession).where(UserSession.expires_at < now))
        session.execute(delete(MetricSample).where(MetricSample.collected_at < cutoff))


def start_scheduler() -> BackgroundScheduler | None:
    settings = get_settings()
    if not settings.run_scheduler:
        logger.info("scheduler disabled")
        return None
    workers = int(os.getenv("WEB_CONCURRENCY", "1"))
    if workers != 1:
        logger.warning("scheduler with WEB_CONCURRENCY=%s may run duplicate jobs; use one worker", workers)
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(check_offline, "interval", seconds=60, id="offline-check", max_instances=1)
    scheduler.add_job(cleanup_expired_data, "interval", days=1, id="data-cleanup", max_instances=1)
    scheduler.start()
    logger.info("scheduler enabled; single worker required")
    return scheduler
