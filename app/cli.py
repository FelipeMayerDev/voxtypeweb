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


def read_markdown(meeting_id: str) -> str:
    """Transcript body as markdown, via voxtype's own export (resolves data via XDG,
    so it works inside the container). Drops the redundant '# Meeting' / '## Transcript'
    headings; the page already shows the metadata header."""
    text = _run(
        "meeting", "export", meeting_id, "-f", "markdown", "--timestamps", "--speakers"
    ).stdout.decode("utf-8", "replace")
    _, sep, body = text.partition("## Transcript")
    return (body if sep else text).strip()
