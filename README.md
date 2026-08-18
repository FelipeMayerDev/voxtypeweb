# Voxtype Web

A web interface (Docker) for the **Voxtype** CLI/TUI app already installed on the host:
edit its config and view meetings (including live). No authentication; it only checks
whether voxtype is installed and whether the daemon is running.

Voxtype itself — binary, config, and meeting data — stays on the host. This container
never captures audio or runs the daemon and is **read-only** over voxtype data: it lists
and shows meetings from `index.db`, renders transcripts via `voxtype meeting export`, and
edits the config TOML. Renaming speakers is an app-owned display alias (voxtype only
labels diarized `SPEAKER_NN`, which this channel-based build doesn't produce). See
`docs/adr/` and `docs/DATA.md` for the full contract.

## Run

Requires voxtype installed on the host at `/usr/bin/voxtype` (→ `/usr/lib/voxtype/<variant>`),
with at least one meeting recorded so `~/.local/share/voxtype/meetings/index.db` exists.

```sh
mkdir -p ~/.local/state/voxtypeweb   # app state (speaker aliases); must be owned by you (uid 1000)
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
| `VOXTYPEWEB_STATE_DIR` | `~/.local/state/voxtypeweb` (speaker aliases) |

## Why Fedora 44 in the Dockerfile

The container bind-mounts the host's `voxtype` binary rather than shipping its own
(ADR 0002) — recording depends on host audio hardware and the daemon, which is out of
scope for the web UI. That means the container's glibc must be compatible with the
binary it's mounting: the host runs glibc 2.43, and current Debian/Ubuntu base images
(glibc 2.41) are too old to execute it. Fedora 44 matches. Swapping the base image for
one with an older glibc will break the mounted binary.

## Docker topology

One service, no audio devices. Host data/config are mounted at their **same absolute
paths** inside the container, because `index.db` stores host-absolute `storage_path`s
that the `voxtype` CLI dereferences to read transcripts:

- `/usr/bin/voxtype` + `/usr/lib/voxtype` — binary, libs, models (`ro`)
- `~/.local/share/voxtype` — meetings + `index.db` (`ro`)
- `~/.config/voxtype` — config TOML (`rw`, so config edits save back to the host)
- `$XDG_RUNTIME_DIR/voxtype` → `/run/voxtype` — daemon state, for the healthcheck (`ro`)
- `~/.local/state/voxtypeweb` — app-owned speaker aliases (`rw`); pre-create it owned by uid 1000

The image also installs the mounted binary's runtime libs (`alsa-lib`, `libstdc++`).
The container runs as UID 1000 so files saved from the web UI are owned by the host user.
