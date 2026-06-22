import json
import os
from config.paths import BASE_DIR

CONFIG_FILE = os.path.join(BASE_DIR, 'content', 'config.json')

_DEFAULTS = {
    'sleep_timeout_min': 5,
    'default_font_size': 'medium',
    'daybook_url': 'http://100.67.252.76:8000',
    'daily_goal_pages': 10,
}


def _load():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Fill in any missing keys from defaults
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULTS)


def _save(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get(key, fallback=None):
    return _load().get(key, fallback if fallback is not None else _DEFAULTS.get(key))


def set(key, value):
    data = _load()
    data[key] = value
    _save(data)


def all_settings():
    return _load()
