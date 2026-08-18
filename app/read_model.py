import sqlite3
from datetime import datetime, timezone

from app.config import INDEX_DB
from app.models import Meeting


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{INDEX_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _to_dt(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _row_to_meeting(row: sqlite3.Row) -> Meeting:
    return Meeting(
        id=row["id"],
        title=row["title"],
        started_at=_to_dt(row["started_at"]),
        ended_at=_to_dt(row["ended_at"]),
        duration_secs=row["duration_secs"],
        status=row["status"],
        chunk_count=row["chunk_count"],
        storage_path=row["storage_path"],
        audio_retained=bool(row["audio_retained"]),
        model=row["model"],
    )


def list_meetings() -> list[Meeting]:
    if not INDEX_DB.exists():
        return []
    with _connect() as con:
        rows = con.execute("SELECT * FROM meetings ORDER BY started_at DESC").fetchall()
    return [_row_to_meeting(row) for row in rows]


def get_meeting(meeting_id: str) -> Meeting | None:
    # Metadata comes straight from index.db (self-contained). The transcript is read
    # via the voxtype CLI markdown export in routes, not from storage_path files — the
    # DB's storage_path is host-absolute and does not exist inside the container.
    if not INDEX_DB.exists():
        return None
    with _connect() as con:
        row = con.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    return _row_to_meeting(row) if row else None
