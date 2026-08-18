# Data & interface contract

Ground truth, inspected from a live voxtype install. Follow this over the CONTEXT.md
glossary casing — real on-disk fields are **snake_case**.

## On-disk layout (host)

```
~/.local/share/voxtype/
  meetings/
    index.db                       # SQLite index (see below)
    <YYYY-MM-DD-slug>/             # one dir per meeting
      metadata.json
      transcript.json
~/.config/voxtype/config.toml      # commented TOML (rw)
$XDG_RUNTIME_DIR/voxtype/          # daemon state (ro)
  state                            # "idle" | "recording" | "transcribing"
  meeting_state                    # same vocabulary
  pid                              # daemon pid
/usr/bin/voxtype -> /usr/lib/voxtype/<variant>   # binary (ro)
```

Note: `index.db` is under `meetings/`, NOT directly under the data dir (ADR 0001 was
imprecise; this file is authoritative).

## `index.db` — table `meetings`

```sql
id TEXT PRIMARY KEY,            -- UUID; use as the meeting id everywhere
title TEXT,                     -- nullable -> render "(untitled)"
started_at INTEGER NOT NULL,    -- unix seconds
ended_at INTEGER,               -- unix seconds, nullable
duration_secs INTEGER,
status TEXT NOT NULL,           -- active | paused | completed | cancelled
chunk_count INTEGER NOT NULL,
storage_path TEXT,              -- absolute dir with metadata/transcript json
audio_retained INTEGER NOT NULL,-- 0/1 -> bool
model TEXT,                     -- engine, e.g. "parakeet"
synced_at INTEGER,
created_at INTEGER NOT NULL
```

List order: `ORDER BY started_at DESC`.

## `index.db` — table `speaker_labels`

```sql
meeting_id TEXT NOT NULL,
speaker_num INTEGER NOT NULL,   -- numeric id; CLI label maps "SPEAKER_00"/"0"
label TEXT NOT NULL,
created_at INTEGER NOT NULL,
PRIMARY KEY (meeting_id, speaker_num)
```

## `metadata.json`

```json
{ "id": "uuid", "title": "teste", "started_at": "2026-08-18T15:35:40.9Z",
  "ended_at": "...Z", "duration_secs": 38, "status": "completed",
  "chunk_count": 2, "storage_path": "/abs/dir", "audio_retained": false,
  "model": "parakeet" }
```
Timestamps here are ISO-8601 (db has unix seconds) — normalize both to datetime.

## `transcript.json`

```json
{ "segments": [
    { "id": 0, "start_ms": 2320, "end_ms": 11520, "text": "...",
      "source": "microphone", "speaker_id": "You", "confidence": 1.0, "chunk_id": 0 },
    { "id": 1, "start_ms": 11520, "end_ms": 15520, "text": "...",
      "source": "microphone", "chunk_id": 0 }        // speaker_id/confidence optional
  ],
  "total_chunks": 2 }
```
`source` ∈ `microphone` | `loopback`. Segments may omit `speaker_id`, `confidence`.

## CLI mutation surface (ADR 0001: mutate via CLI only)

```
voxtype meeting export <ID|latest> -f text|markdown|json [--timestamps --speakers --metadata]  # stdout
voxtype meeting label  <ID|latest> <SPEAKER_ID> <LABEL>
voxtype meeting delete <ID> -f
```
Reads (list/show/live) NEVER shell out — read index.db + json directly. NEVER write
index.db or the json files.

## HTTP + template contract (both workers follow exactly)

Single FastAPI service, no auth, Jinja2 server-rendered + HTMX, port 8000,
entrypoint `app.main:app`.

### Paths / settings (`app/config.py`, env with host defaults)

| env | default |
|---|---|
| `VOXTYPE_DATA_DIR` | `~/.local/share/voxtype` |
| (derived) `MEETINGS_DIR` | `$VOXTYPE_DATA_DIR/meetings` |
| (derived) `INDEX_DB` | `$MEETINGS_DIR/index.db` |
| `VOXTYPE_CONFIG_PATH` | `~/.config/voxtype/config.toml` |
| `VOXTYPE_BIN` | `/usr/bin/voxtype` |
| `VOXTYPE_STATE_DIR` | `$XDG_RUNTIME_DIR/voxtype` |

### Routes

| method | path | returns | notes |
|---|---|---|---|
| GET | `/` | `index.html` | ctx: `meetings: list[Meeting]`, `health: Health` |
| GET | `/meetings/{id}` | `meeting.html` | ctx: `meeting: MeetingDetail`, `health: Health` |
| GET | `/meetings/{id}/transcript` | `_transcript.html` | HTMX poll target; ctx: `meeting: MeetingDetail` |
| POST | `/meetings/{id}/label` | redirect to detail | form: `speaker_id`, `label` -> CLI label |
| POST | `/meetings/{id}/delete` | redirect to `/` | CLI delete -f |
| GET | `/meetings/{id}/export` | file download | query `format=text\|markdown\|json`; CLI export |
| GET | `/config` | `config.html` | ctx: `content: str`, `error: str\|None`, `saved: bool` |
| POST | `/config` | `config.html` | form: `content`; validate `tomlkit.parse`, write raw text (comments preserved) |
| GET | `/health` | JSON `Health` | binary present + daemon state |

### Pydantic models (`app/models.py`)

- `Segment`: `id:int, start_ms:int, end_ms:int, text:str, source:str, speaker_id:str|None=None, confidence:float|None=None, chunk_id:int|None=None`
- `SpeakerLabel`: `meeting_id:str, speaker_num:int, label:str`
- `Meeting`: `id:str, title:str|None, started_at:datetime, ended_at:datetime|None, duration_secs:int|None, status:str, chunk_count:int, storage_path:str|None, audio_retained:bool, model:str|None`
- `MeetingDetail`: all `Meeting` fields + `segments:list[Segment]`, `labels:list[SpeakerLabel]`, `total_chunks:int`
- `DaemonState`: `state:str, meeting_state:str|None, pid:int|None, running:bool`
- `Health`: `ok:bool, binary_present:bool, binary_path:str, daemon:DaemonState`

### Templates (`templates/`)

- `base.html`: layout; `<head>` loads `/static/style.css` + `/static/htmx.min.js`; nav (Home `/`, Config `/config`); renders `_health.html` banner from `health`; `{% block content %}`.
- `index.html` extends base: table of `meetings` — title (or "(untitled)"), started_at, duration, status badge, chunk_count, model, actions (view, export text/md/json links, delete POST form).
- `meeting.html` extends base: metadata header + `_transcript.html`. If `meeting.status in ("active","paused")`, wrap transcript in a container with `hx-get="/meetings/{id}/transcript" hx-trigger="every 5s" hx-swap="innerHTML"`. Speaker-label form (POST `/meetings/{id}/label`, fields `speaker_id`, `label`).
- `_transcript.html`: renders `meeting.segments` — timestamp `mm:ss` from `start_ms`, speaker (label for `speaker_id` if present else raw `speaker_id`), source icon (mic/loopback), text.
- `config.html` extends base: `<form method=post action="/config">` with big monospace `<textarea name="content">{{ content }}</textarea>` + Save; show `error` if invalid TOML, success if `saved`.
- `_health.html`: banner from `health` — green if `ok`, shows daemon `state`; warn/red if binary missing.

### Static (`static/`)

- `style.css`: minimal clean styling (system font, readable transcript, status badges).
- `htmx.min.js`: vendor htmx (~14KB) so the container needs no CDN at runtime.

### Deps

`fastapi`, `uvicorn[standard]`, `jinja2`, `tomlkit`, `python-multipart` (form posts). `sqlite3` is stdlib.

## Docker (ADR 0002)

- `Dockerfile`: `FROM fedora:44`; install python3 + pip; create user uid 1000; copy `app/`,
  `templates/`, `static/`; `pip install` deps; `USER 1000`; `EXPOSE 8000`;
  `CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]`.
  Fedora 44 base is REQUIRED (host glibc 2.43; Debian/Ubuntu glibc too old for the mounted binary).
- `docker-compose.yml`: service runs as `user: "1000:1000"`, `ports: "8000:8000"`, and bind-mounts
  (map to the container paths the env vars point at):
  - `/usr/bin/voxtype:/usr/bin/voxtype:ro`
  - `/usr/lib/voxtype:/usr/lib/voxtype:ro`
  - `${HOME}/.local/share/voxtype:/data/voxtype:ro`  + `VOXTYPE_DATA_DIR=/data/voxtype`
  - `${HOME}/.config/voxtype:/config/voxtype:rw`      + `VOXTYPE_CONFIG_PATH=/config/voxtype/config.toml`
  - `${XDG_RUNTIME_DIR}/voxtype:/run/voxtype:ro`       + `VOXTYPE_STATE_DIR=/run/voxtype`
  - healthcheck hitting `/health`.
