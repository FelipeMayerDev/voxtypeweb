import subprocess

from app.config import VOXTYPE_BIN


class VoxtypeCliError(RuntimeError):
    pass


def _run(*args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [str(VOXTYPE_BIN), *args],
        capture_output=True,
    )
    if result.returncode != 0:
        raise VoxtypeCliError(
            f"voxtype {' '.join(args)} failed (exit {result.returncode}): "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result


def export(meeting_id: str, fmt: str) -> bytes:
    return _run("meeting", "export", meeting_id, "-f", fmt).stdout
