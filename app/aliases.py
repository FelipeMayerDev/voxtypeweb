"""App-owned speaker aliases: speaker_id (e.g. "You"/"Remote") -> display name,
per meeting. voxtype attributes speakers by channel and its numeric `meeting
label` can't rename them, so we remap at display time. Purely presentational;
stored outside the voxtype dirs.
"""

import json
import os

from app.config import SPEAKER_ALIASES_PATH


def _load() -> dict:
    try:
        data = json.loads(SPEAKER_ALIASES_PATH.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_aliases(meeting_id: str) -> dict[str, str]:
    aliases = _load().get(meeting_id, {})
    return aliases if isinstance(aliases, dict) else {}


def set_alias(meeting_id: str, speaker_id: str, name: str) -> None:
    """Set (or, with an empty name, clear) the alias for one speaker."""
    data = _load()
    meeting = data.setdefault(meeting_id, {})
    if name:
        meeting[speaker_id] = name
    else:
        meeting.pop(speaker_id, None)
    if not meeting:
        data.pop(meeting_id, None)

    SPEAKER_ALIASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SPEAKER_ALIASES_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    os.replace(tmp, SPEAKER_ALIASES_PATH)


def apply_aliases(markdown_body: str, aliases: dict[str, str]) -> str:
    """Rewrite `### <speaker_id>` transcript headings to the aliased name."""
    if not aliases:
        return markdown_body
    lines = []
    for line in markdown_body.split("\n"):
        if line.startswith("### "):
            speaker = line[4:].strip()
            lines.append(f"### {aliases.get(speaker, speaker)}")
        else:
            lines.append(line)
    return "\n".join(lines)
