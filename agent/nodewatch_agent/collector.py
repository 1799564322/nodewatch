import platform
import socket
from datetime import UTC, datetime
import time
import uuid

import psutil

from nodewatch_agent import __version__


def collect_system_info() -> dict[str, object]:
    return {
        "hostname": socket.gethostname(),
        "os_name": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_model": platform.processor() or None,
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_logical_cores": psutil.cpu_count(logical=True),
        "memory_total_bytes": psutil.virtual_memory().total,
        "agent_version": __version__,
    }


class MetricsCollector:
    def __init__(self) -> None:
        self.previous_net = psutil.net_io_counters()
        self.previous_time = time.monotonic()

    def collect(self) -> dict[str, object]:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        root = psutil.disk_usage("C:\\" if platform.system() == "Windows" else "/")
        current_net = psutil.net_io_counters()
        current_time = time.monotonic()
        elapsed = max(current_time - self.previous_time, 0.001)
        tx_rate = max(0, int((current_net.bytes_sent - self.previous_net.bytes_sent) / elapsed))
        rx_rate = max(0, int((current_net.bytes_recv - self.previous_net.bytes_recv) / elapsed))
        self.previous_net, self.previous_time = current_net, current_time
        disks = []
        seen = set()
        for partition in psutil.disk_partitions(all=False):
            if partition.mountpoint in seen:
                continue
            seen.add(partition.mountpoint)
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except (OSError, PermissionError):
                continue
            disks.append(
                {
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype or None,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "percent": usage.percent,
                }
            )
        return {
            "sample_id": str(uuid.uuid4()),
            "collected_at": datetime.now(UTC).isoformat(),
            "cpu_percent": cpu,
            "memory_percent": memory.percent,
            "memory_used_bytes": memory.used,
            "swap_percent": swap.percent,
            "root_disk_percent": root.percent,
            "root_disk_used_bytes": root.used,
            "net_tx_bytes_per_sec": tx_rate,
            "net_rx_bytes_per_sec": rx_rate,
            "uptime_seconds": max(0, int(time.time() - psutil.boot_time())),
            "disks": disks,
        }
