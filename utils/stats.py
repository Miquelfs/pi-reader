import json
import os
from datetime import date, timedelta
from config.paths import BASE_DIR

STATS_FILE = os.path.join(BASE_DIR, 'content', 'stats.json')


def _load():
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(sessions):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def record_session(book, pages, words, duration_s):
    if pages <= 0:
        return
    sessions = _load()
    sessions.append({
        'date': date.today().isoformat(),
        'book': book,
        'pages': pages,
        'words': words,
        'duration_s': int(duration_s),
    })
    _save(sessions)


def load_stats():
    return _load()


def streak_days():
    """Return the current daily reading streak (consecutive days ending today or yesterday)."""
    sessions = _load()
    if not sessions:
        return 0
    read_dates = sorted({s['date'] for s in sessions}, reverse=True)
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    # Streak must include today or yesterday to be active
    if read_dates[0] not in (today, yesterday):
        return 0
    streak = 1
    for i in range(1, len(read_dates)):
        prev = date.fromisoformat(read_dates[i - 1])
        curr = date.fromisoformat(read_dates[i])
        if (prev - curr).days == 1:
            streak += 1
        else:
            break
    return streak


def total_pages():
    return sum(s['pages'] for s in _load())


def total_words():
    return sum(s['words'] for s in _load())


def total_hours():
    return sum(s['duration_s'] for s in _load()) / 3600


def last_session():
    sessions = _load()
    return sessions[-1] if sessions else None


def read_today():
    today = date.today().isoformat()
    return any(s['date'] == today for s in _load())
