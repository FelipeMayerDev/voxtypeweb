import os
from pathlib import Path


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser()


DATA_DIR = _env_path("VOXTYPE_DATA_DIR", "~/.local/share/voxtype")
MEETINGS_DIR = DATA_DIR / "meetings"
INDEX_DB = MEETINGS_DIR / "index.db"

CONFIG_PATH = _env_path("VOXTYPE_CONFIG_PATH", "~/.config/voxtype/config.toml")
VOXTYPE_BIN = _env_path("VOXTYPE_BIN", "/usr/bin/voxtype")
STATE_DIR = _env_path("VOXTYPE_STATE_DIR", os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"), "voxtype"))

# App-owned state (speaker aliases): NOT voxtype data, so it stays out of the
# voxtype dirs. voxtype attributes speakers by channel (You/Remote), so its
# numeric `meeting label` can't rename them — we alias at display time instead.
WEB_STATE_DIR = _env_path("VOXTYPEWEB_STATE_DIR", "~/.local/state/voxtypeweb")
SPEAKER_ALIASES_PATH = WEB_STATE_DIR / "speaker-aliases.json"
