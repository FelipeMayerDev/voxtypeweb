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


def label(meeting_id: str, speaker_id: str, label: str) -> None:
    _run("meeting", "label", meeting_id, speaker_id, label)


def delete(meeting_id: str) -> None:
    _run("meeting", "delete", meeting_id, "-f")
