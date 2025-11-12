"""Shared utility for persisting simple user preferences across CLI runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


PREFERENCES_FILE = Path(__file__).resolve().parent.parent / "cli_preferences.json"


def _load_preferences() -> Dict[str, Any]:
    try:
        with PREFERENCES_FILE.open("r", encoding="utf-8") as preferences_file:
            data = json.load(preferences_file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _save_preferences(preferences: Dict[str, Any]) -> None:
    with PREFERENCES_FILE.open("w", encoding="utf-8") as preferences_file:
        json.dump(preferences, preferences_file, indent=2)


_PREFERENCES: Dict[str, Any] = _load_preferences()


def get_bool(key: str) -> Optional[bool]:
    """Return a stored boolean preference if available."""

    value = _PREFERENCES.get(key)
    return value if isinstance(value, bool) else None


def remember_bool(key: str, value: bool) -> None:
    """Persist a boolean preference."""

    _PREFERENCES[key] = bool(value)
    _save_preferences(_PREFERENCES)


def get_int(key: str) -> Optional[int]:
    """Return a stored integer preference if available."""

    value = _PREFERENCES.get(key)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def remember_int(key: str, value: int) -> None:
    """Persist an integer preference."""

    try:
        _PREFERENCES[key] = int(value)
    except (TypeError, ValueError):
        return
    _save_preferences(_PREFERENCES)


def forget(key: str) -> None:
    """Remove a stored preference."""

    if key in _PREFERENCES:
        del _PREFERENCES[key]
        _save_preferences(_PREFERENCES)
