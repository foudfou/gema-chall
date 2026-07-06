"""Database storage for processed events."""

import sqlite3
from pathlib import Path

import pandas as pd
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from pipeline.models import EnrichedPlayEvent

log = structlog.get_logger()


class Database:
    """
    Base class for database backends.

    For async implementation, you would:
    1. Create an AsyncDatabase with:
           async def store_batch(self, events: list[EnrichedPlayEvent]) -> int: ...
    2. Use asyncpg or aiosqlite for async DB access
    """

    def store_batch(self, events: list[EnrichedPlayEvent]) -> int:
        """Store a batch of events. Returns the number stored."""
        raise NotImplementedError


class SqliteDatabase(Database):
    """SQLite implementation."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS play_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        isrc_code TEXT NOT NULL,
        station_id TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        listener_count INTEGER NOT NULL,
        artist TEXT NOT NULL,
        title TEXT NOT NULL,
        rights_holder TEXT NOT NULL,
        listened_seconds INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_play_events_isrc ON play_events(isrc_code);
    CREATE INDEX IF NOT EXISTS idx_play_events_timestamp ON play_events(timestamp);
    CREATE INDEX IF NOT EXISTS idx_play_events_station ON play_events(station_id);
    """

    def __init__(self, db_path: str | Path = "play_events.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.SCHEMA)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=2),
        reraise=True,
    )
    def store_batch(self, events: list[EnrichedPlayEvent]) -> int:
        if not events:
            return 0

        df = pd.DataFrame([e.model_dump() for e in events])
        df["timestamp"] = df["timestamp"].astype(str)

        with sqlite3.connect(self.db_path) as conn:
            df.to_sql("play_events", conn, if_exists="append", index=False)

        log.info("batch_stored", count=len(events))
        return len(events)
