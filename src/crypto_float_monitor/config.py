"""Persistent configuration helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

CONFIG_DIR_NAME: Final[str] = "crypto-float-monitor"
CONFIG_FILE_NAME: Final[str] = "config.json"
DEFAULT_CONFIG: Final[dict[str, object]] = {
    "symbol": "BTCUSDT",
    "alert_above": None,
    "alert_below": None,
}


def _config_base_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".config"


def _config_file_path() -> Path:
    return _config_base_dir() / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def _ensure_config_file() -> dict[str, object]:
    path = _config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        _write_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("config must be an object")
    except Exception:
        raw = DEFAULT_CONFIG.copy()
        _write_config(raw)
    return {**DEFAULT_CONFIG, **raw}


def _write_config(data: dict[str, object]) -> None:
    path = _config_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _coerce_threshold(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


@dataclass(frozen=True)
class AppConfig:
    symbol: str
    alert_above: float | None
    alert_below: float | None


def load_config() -> AppConfig:
    data = _ensure_config_file()
    symbol = str(data.get("symbol", DEFAULT_CONFIG["symbol"]))
    alert_above = _coerce_threshold(data.get("alert_above"))
    alert_below = _coerce_threshold(data.get("alert_below"))
    return AppConfig(
        symbol=symbol.upper(),
        alert_above=alert_above,
        alert_below=alert_below,
    )


def save_alerts(alert_above: float | None, alert_below: float | None) -> None:
    data = _ensure_config_file()
    data["alert_above"] = alert_above
    data["alert_below"] = alert_below
    _write_config(data)
