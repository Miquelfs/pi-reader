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


def record_session(book, pages, words, duration_s, rsvp_words=0, rsvp_duration_s=0):
    if pages <= 0 and rsvp_words <= 0:
        return
    sessions = _load()
    entry = {
        'date': date.today().isoformat(),
        'book': book,
        'pages': pages,
        'words': words,
        'duration_s': int(duration_s),
        'avg_s_per_page': round(duration_s / pages, 1) if pages > 0 else 0,
        'rsvp_words': rsvp_words,
        'rsvp_duration_s': int(rsvp_duration_s),
    }
    sessions.append(entry)
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


def avg_s_per_page():
    sessions = [s for s in _load() if s.get('pages', 0) > 0]
    if not sessions:
        return 0.0
    total_dur = sum(s['duration_s'] for s in sessions)
    total_pg  = sum(s['pages'] for s in sessions)
    return total_dur / total_pg if total_pg else 0.0


def total_rsvp_words():
    return sum(s.get('rsvp_words', 0) for s in _load())


def rsvp_time_pct():
    sessions = _load()
    total_dur = sum(s['duration_s'] for s in sessions)
    rsvp_dur  = sum(s.get('rsvp_duration_s', 0) for s in sessions)
    if total_dur + rsvp_dur == 0:
        return 0.0
    return 100.0 * rsvp_dur / (total_dur + rsvp_dur)


def read_today():
    today = date.today().isoformat()
    return any(s['date'] == today for s in _load())
