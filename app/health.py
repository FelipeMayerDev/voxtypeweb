import os

from app.config import STATE_DIR, VOXTYPE_BIN
from app.models import DaemonState, Health


def get_daemon_state() -> DaemonState:
    state_file = STATE_DIR / "state"
    meeting_state_file = STATE_DIR / "meeting_state"
    pid_file = STATE_DIR / "pid"

    state = state_file.read_text().strip() if state_file.exists() else "unknown"
    meeting_state = meeting_state_file.read_text().strip() if meeting_state_file.exists() else None

    pid: int | None = None
    running = False
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
        except ValueError:
            pid = None
        if pid is not None:
            try:
                os.kill(pid, 0)
                running = True
            except ProcessLookupError:
                running = False
            except PermissionError:
                running = True

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
