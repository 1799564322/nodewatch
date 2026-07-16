import random

from nodewatch_agent.retry import ExponentialBackoff


def test_backoff_is_bounded_and_resettable() -> None:
    backoff = ExponentialBackoff(maximum=4, random_source=random.Random(1))
    delays = [backoff.next_delay() for _ in range(10)]
    assert all(0 <= delay <= 4 for delay in delays)
    assert backoff.attempt == 10
    backoff.reset()
    assert backoff.attempt == 0
