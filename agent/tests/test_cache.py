from datetime import UTC, datetime, timedelta

from nodewatch_agent.cache import MetricCache


def metric(sample_id: str, collected_at: datetime) -> dict:
    return {"sample_id": sample_id, "collected_at": collected_at.isoformat()}


def test_cache_orders_samples_and_survives_reopen(tmp_path) -> None:
    path = tmp_path / "metrics.db"
    now = datetime.now(UTC)
    cache = MetricCache(path, max_samples=10, retention_days=7)
    cache.enqueue(metric("later", now + timedelta(minutes=1)))
    cache.enqueue(metric("earlier", now))
    cache.close()

    reopened = MetricCache(path, max_samples=10, retention_days=7)
    assert [item["sample_id"] for item in reopened.oldest(10)] == ["earlier", "later"]
    reopened.remove(["earlier"])
    assert reopened.count() == 1
    reopened.close()


def test_cache_enforces_sample_limit(tmp_path) -> None:
    cache = MetricCache(tmp_path / "metrics.db", max_samples=2, retention_days=7)
    now = datetime.now(UTC)
    for index in range(3):
        cache.enqueue(metric(str(index), now + timedelta(minutes=index)))

    assert [item["sample_id"] for item in cache.oldest(10)] == ["1", "2"]
    cache.close()
