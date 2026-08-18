from datetime import datetime

from pydantic import BaseModel


class Segment(BaseModel):
    id: int
    start_ms: int
    end_ms: int
    text: str
    source: str
    speaker_id: str | None = None
    confidence: float | None = None
    chunk_id: int | None = None


class SpeakerLabel(BaseModel):
    meeting_id: str
    speaker_num: int
    label: str


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


class MeetingDetail(Meeting):
    segments: list[Segment]
    labels: list[SpeakerLabel]
    total_chunks: int


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
