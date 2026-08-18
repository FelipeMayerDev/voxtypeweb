from datetime import datetime

from pydantic import BaseModel


class Meeting(BaseModel):
    id: str
    title: str | None
    started_at: datetime
    ended_at: datetime | None
    duration_secs: int | None
    status: str
    chunk_count: int
    storage_path: str | None
    audio_retained: bool
    model: str | None


class DaemonState(BaseModel):
    state: str
    meeting_state: str | None
    pid: int | None
    running: bool


class Health(BaseModel):
    ok: bool
    binary_present: bool
    binary_path: str
    daemon: DaemonState
