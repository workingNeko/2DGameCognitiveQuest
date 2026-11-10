# core/settings_manager.py
"""
Game & System Settings Manager for Cognitive Quest 2D.
Manages persistent options such as:
- Objective Finder Guide (Visual trail & compass indicators - default: False / Disabled)
- Music & SFX audio settings synchronization
"""

import os
import json
import threading
from .paths import get_base_dir

_SETTINGS_LOCK = threading.RLock()
_CACHED_SETTINGS = None


def _get_settings_path():
    base_dir = get_base_dir()
    return os.path.join(base_dir, "db", "saves", "audio_settings.json")


def load_settings(force_reload=False):
    """Load settings from disk with robust caching and defaults."""
    global _CACHED_SETTINGS
    with _SETTINGS_LOCK:
        if _CACHED_SETTINGS is not None and not force_reload:
            return dict(_CACHED_SETTINGS)

        defaults = {
            "music_volume": 0.5,
            "sfx_volume": 0.7,
            "music_muted": False,
            "sfx_muted": False,
            "objective_finder": False,  # Optional in settings, removed by default
        }

        path = _get_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    disk_data = json.load(f)
                    if isinstance(disk_data, dict):
                        defaults.update(disk_data)
            except Exception as e:
                print(f"[WARN] SettingsManager: Error reading settings from {path}: {e}")

        # Ensure objective_finder is strictly boolean
        defaults["objective_finder"] = bool(defaults.get("objective_finder", False))
        _CACHED_SETTINGS = defaults
        return dict(_CACHED_SETTINGS)


def save_settings(data=None):
    """Persist settings to disk atomically."""
    global _CACHED_SETTINGS
    with _SETTINGS_LOCK:
        current = load_settings()
        if data and isinstance(data, dict):
            current.update(data)

        current["objective_finder"] = bool(current.get("objective_finder", False))
        _CACHED_SETTINGS = current

        path = _get_settings_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            temp_path = f"{path}.tmp_{os.getpid()}"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=4)
            os.replace(temp_path, path)
        except Exception as e:
            print(f"[WARN] SettingsManager: Error saving settings to {path}: {e}")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(current, f, indent=4)
            except Exception:
                pass


def is_objective_finder_enabled():
    """Returns True if the Objective Finder guide (trail and compass) is enabled. Default: False."""
    settings = load_settings()
    return bool(settings.get("objective_finder", False))


def set_objective_finder_enabled(enabled):
    """Sets whether the Objective Finder guide is enabled and saves to disk."""
    val = bool(enabled)
    with _SETTINGS_LOCK:
        settings = load_settings()
        settings["objective_finder"] = val
        save_settings(settings)
    return val


def toggle_objective_finder():
    """Toggles the Objective Finder guide on/off and returns the new state."""
    curr = is_objective_finder_enabled()
    return set_objective_finder_enabled(not curr)

