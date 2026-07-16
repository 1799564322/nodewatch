from nodewatch_agent.collector import MetricsCollector


def test_metric_values_have_valid_ranges() -> None:
    metric = MetricsCollector().collect()
    assert 0 <= metric["cpu_percent"] <= 100
    assert 0 <= metric["memory_percent"] <= 100
    assert metric["memory_used_bytes"] >= 0
    assert metric["net_tx_bytes_per_sec"] >= 0
    assert metric["net_rx_bytes_per_sec"] >= 0
    assert metric["uptime_seconds"] >= 0
