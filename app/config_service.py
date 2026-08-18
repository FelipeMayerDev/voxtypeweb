import os
import tempfile

import tomlkit

from app.config import CONFIG_PATH


class ConfigError(ValueError):
    pass


def read_config() -> str:
    return CONFIG_PATH.read_text()


def write_config(text: str) -> None:
    try:
        tomlkit.parse(text)
    except tomlkit.exceptions.TOMLKitError as exc:
        raise ConfigError(f"Invalid TOML: {exc}") from exc

    fd, tmp_path = tempfile.mkstemp(
        dir=CONFIG_PATH.parent, prefix=f".{CONFIG_PATH.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp_path, CONFIG_PATH)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
