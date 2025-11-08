"""Persistent configuration helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

CONFIG_DIR_NAME: Final[str] = "crypto-float-monitor"
CONFIG_FILE_NAME: Final[str] = "config.json"
DEFAULT_CONFIG: Final[dict[str, str]] = {"symbol": "BTCUSDT"}


def _config_base_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".config"


def _config_file_path() -> Path:
    return _config_base_dir() / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def _ensure_config_file() -> dict[str, str]:
    path = _config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return DEFAULT_CONFIG.copy()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("config must be an object")
    except Exception:
        raw = DEFAULT_CONFIG.copy()
        path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return {**DEFAULT_CONFIG, **raw}


@dataclass(frozen=True)
class AppConfig:
    symbol: str


def load_config() -> AppConfig:
    data = _ensure_config_file()
    symbol = str(data.get("symbol", DEFAULT_CONFIG["symbol"]))
    return AppConfig(symbol=symbol.upper())
