"""Embedded media assets for Crypto Float Monitor."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

_ASSET_PACKAGE = __name__


def get_asset_path(filename: str) -> Path:
    """Return a filesystem path for a packaged asset."""
    asset = resources.files(_ASSET_PACKAGE).joinpath(filename)
    return Path(asset)
