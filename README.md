# Voxtype Web

A web interface (Docker) for the **Voxtype** CLI/TUI app already installed on the host:
edit its config and view meetings (including live). No authentication; it only checks
whether voxtype is installed and whether the daemon is running.

Voxtype itself — binary, config, and meeting data — stays on the host. This container
never captures audio or runs the daemon; it is view-only for meetings and mutates state
strictly through the `voxtype` CLI (export/label/delete), never by writing `index.db` or
the meeting JSON files directly. See `docs/adr/0001-hybrid-read-model.md` and
`docs/DATA.md` for the full contract.

## Run

Requires voxtype installed on the host at `/usr/bin/voxtype` (→ `/usr/lib/voxtype/<variant>`),
with at least one meeting recorded so `~/.local/share/voxtype/meetings/index.db` exists.

```sh
docker compose up --build
```

Then open http://localhost:8000.

To run without Docker (Python 3.12+):

```sh
pip install -e .
uvicorn app.main:app --reload
```

### Configuration

All settings are environment variables with host-friendly defaults (see `app/config.py`
and `docs/DATA.md`):

| env | default |
|---|---|
| `VOXTYPE_DATA_DIR` | `~/.local/share/voxtype` |
| `VOXTYPE_CONFIG_PATH` | `~/.config/voxtype/config.toml` |
| `VOXTYPE_BIN` | `/usr/bin/voxtype` |
| `VOXTYPE_STATE_DIR` | `$XDG_RUNTIME_DIR/voxtype` |

## Why Fedora 44 in the Dockerfile

The container bind-mounts the host's `voxtype` binary rather than shipping its own
(ADR 0002) — recording depends on host audio hardware and the daemon, which is out of
scope for the web UI. That means the container's glibc must be compatible with the
binary it's mounting: the host runs glibc 2.43, and current Debian/Ubuntu base images
(glibc 2.41) are too old to execute it. Fedora 44 matches. Swapping the base image for
one with an older glibc will break the mounted binary.

## Docker topology

One service, no audio devices, five bind mounts mapping host paths to the container
paths the env vars above point at:

- `/usr/bin/voxtype` + `/usr/lib/voxtype` — binary, libs, models (`ro`)
- `~/.local/share/voxtype` → `/data/voxtype` — meetings + `index.db` (`ro`)
- `~/.config/voxtype` → `/config/voxtype` — config TOML (`rw`, so config edits save back to the host)
- `$XDG_RUNTIME_DIR/voxtype` → `/run/voxtype` — daemon state, for the healthcheck (`ro`)

The container runs as UID 1000 so config saved from the web UI is owned by the host user.
