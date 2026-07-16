import json
from pathlib import Path
import sqlite3
from typing import Any


class MetricCache:
    def __init__(self, path: Path, max_samples: int, retention_days: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.max_samples = max_samples
        self.retention_days = retention_days
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pending_metrics (
                sample_id TEXT PRIMARY KEY,
                collected_at TEXT NOT NULL,
                payload TEXT NOT NULL,
                queued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()
        self.cleanup()

    def enqueue(self, metric: dict[str, Any]) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT OR IGNORE INTO pending_metrics(sample_id, collected_at, payload) VALUES (?, ?, ?)",
                (metric["sample_id"], metric["collected_at"], json.dumps(metric)),
            )
        self.cleanup()

    def oldest(self, limit: int) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT payload FROM pending_metrics ORDER BY collected_at, sample_id LIMIT ?", (limit,)
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def remove(self, sample_ids: list[str]) -> None:
        if not sample_ids:
            return
        with self.connection:
            self.connection.executemany(
                "DELETE FROM pending_metrics WHERE sample_id = ?",
                [(sample_id,) for sample_id in sample_ids],
            )

    def cleanup(self) -> None:
        with self.connection:
            self.connection.execute(
                "DELETE FROM pending_metrics WHERE queued_at < datetime('now', ?)",
                (f"-{self.retention_days} days",),
            )
            self.connection.execute(
                """
                DELETE FROM pending_metrics WHERE sample_id IN (
                    SELECT sample_id FROM pending_metrics
                    ORDER BY collected_at DESC, sample_id DESC
                    LIMIT -1 OFFSET ?
                )
                """,
                (self.max_samples,),
            )

    def count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM pending_metrics").fetchone()[0])

    def close(self) -> None:
        self.connection.close()
