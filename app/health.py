from app.config import STATE_DIR, VOXTYPE_BIN
from app.models import DaemonState, Health


def get_daemon_state() -> DaemonState:
    state_file = STATE_DIR / "state"
    meeting_state_file = STATE_DIR / "meeting_state"
    pid_file = STATE_DIR / "pid"

    state = state_file.read_text().strip() if state_file.exists() else "unknown"
    meeting_state = meeting_state_file.read_text().strip() if meeting_state_file.exists() else None

    pid: int | None = None
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
        except ValueError:
            pid = None

    # Liveness from the published state file, not os.kill(pid): the daemon runs on the
    # host and this process may be in a container (ADR 0002) where host PIDs are invisible.
    # voxtype's own status integration is file-based; a live daemon publishes one of these.
    # ponytail: trusts the state file; a crash leaving a stale file reads as running.
    running = state in ("idle", "recording", "transcribing")

    return DaemonState(state=state, meeting_state=meeting_state, pid=pid, running=running)


def get_health() -> Health:
    binary_present = VOXTYPE_BIN.exists()
    daemon = get_daemon_state()
    return Health(
        ok=binary_present and daemon.running,
        binary_present=binary_present,
        binary_path=str(VOXTYPE_BIN),
        daemon=daemon,
    )
