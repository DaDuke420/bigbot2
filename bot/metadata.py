"""Persistent metadata helpers for the bot (newsletter, runs, etc.).

Stores a small JSON file under the data directory. Keep this module
minimal: read/write JSON and helpers for `last_newsletter_time`.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from . import config

METADATA_FILENAME = "newsletter_meta.json"


def _metadata_path(storage_dir: Optional[str] = None) -> str:
    dirpath = storage_dir or config.DATA_DIR
    os.makedirs(dirpath, exist_ok=True)
    return os.path.join(dirpath, METADATA_FILENAME)


def _read_metadata(storage_dir: Optional[str] = None) -> Dict:
    path = _metadata_path(storage_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_metadata(data: Dict, storage_dir: Optional[str] = None) -> None:
    path = _metadata_path(storage_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_last_newsletter_time(storage_dir: Optional[str] = None) -> Optional[datetime]:
    """Return the last recorded newsletter time as a timezone-aware datetime or None."""
    data = _read_metadata(storage_dir)
    ts = data.get("last_newsletter_time")
    if not ts:
        return None
    try:
        # fromisoformat supports the format we write below
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            # assume UTC if naive
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def set_last_newsletter_time(dt: datetime, storage_dir: Optional[str] = None) -> None:
    """Record the given datetime (converted to UTC ISO8601) as the last newsletter time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    iso = dt.astimezone(timezone.utc).isoformat()
    data = _read_metadata(storage_dir)
    data["last_newsletter_time"] = iso
    _write_metadata(data, storage_dir)
