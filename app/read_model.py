import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config import INDEX_DB
from app.models import Meeting, MeetingDetail, Segment, SpeakerLabel

_MEETING_JSON_FIELDS = (
    "title", "started_at", "ended_at", "duration_secs", "status",
    "chunk_count", "storage_path", "audio_retained", "model",
)


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


def get_meeting(meeting_id: str) -> MeetingDetail | None:
    if not INDEX_DB.exists():
        return None
    with _connect() as con:
        row = con.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if row is None:
            return None
        label_rows = con.execute(
            "SELECT * FROM speaker_labels WHERE meeting_id = ?", (meeting_id,)
        ).fetchall()

    fields = dict(row)
    storage_path = fields["storage_path"]

    if storage_path:
        metadata_path = Path(storage_path) / "metadata.json"
        if metadata_path.exists():
            meta = json.loads(metadata_path.read_text())
            for key in _MEETING_JSON_FIELDS:
                if key in meta:
                    fields[key] = meta[key]

    segments: list[Segment] = []
    total_chunks = fields["chunk_count"] or 0
    if storage_path:
        transcript_path = Path(storage_path) / "transcript.json"
        if transcript_path.exists():
            transcript = json.loads(transcript_path.read_text())
            segments = [Segment(**seg) for seg in transcript.get("segments", [])]
            total_chunks = transcript.get("total_chunks", total_chunks)

    labels = [
        SpeakerLabel(meeting_id=lr["meeting_id"], speaker_num=lr["speaker_num"], label=lr["label"])
        for lr in label_rows
    ]

    return MeetingDetail(
        id=fields["id"],
        title=fields["title"],
        started_at=_to_dt(fields["started_at"]),
        ended_at=_to_dt(fields["ended_at"]),
        duration_secs=fields["duration_secs"],
        status=fields["status"],
        chunk_count=fields["chunk_count"],
        storage_path=fields["storage_path"],
        audio_retained=bool(fields["audio_retained"]),
        model=fields["model"],
        segments=segments,
        labels=labels,
        total_chunks=total_chunks,
    )
