"""
Today / tomorrow data from Daybook, cached in content/today.json so the Today and
sleep screens still work offline (e.g. travelling without the tailnet).
refresh() does the network calls; the *_view() functions are pure and only read the cache.
"""
import json
import os
import threading
from datetime import date, datetime, timedelta
from config.paths import BASE_DIR

CACHE_FILE = os.path.join(BASE_DIR, 'content', 'today.json')
_refreshing = threading.Lock()

_CONDITIONS = {'sunny': 'sunny', 'partly_cloudy': 'partly cloudy', 'cloudy': 'cloudy',
               'rainy': 'rain', 'stormy': 'storms', 'snowy': 'snow'}
_DUTY = {'flying_duty': 'Flying', 'standby': 'Standby', 'ground_duty': 'Ground duty',
         'day_off': 'Day off', 'vacation': 'Vacation'}


def load():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def refresh(today=None):
    """Fetch everything the screens need. Keeps the previous cache if Daybook is unreachable.
    Returns True if new data was saved."""
    if not _refreshing.acquire(blocking=False):
        return False
    try:
        from utils.daybook_sync import _get
        today = today or date.today()
        t, tm = today.isoformat(), (today + timedelta(days=1)).isoformat()
        agenda = _get('/agenda', {'date': t})
        if agenda is None:
            return False                    # offline: don't wait on the remaining calls
        data = {
            'fetched_at': datetime.now().isoformat(timespec='minutes'),
            'date': t,
            'agenda': agenda,
            'weather': _get('/weather', {'start': t, 'end': tm}) or [],
            'roster': {t: _get(f'/roster/day/{t}/brief'), tm: _get(f'/roster/day/{tm}/brief')},
            'trip_days': _trip_days(_get, t, tm),
            'on_this_day': _get(f'/insights/on-this-day/{t}'),
        }
        tmp = CACHE_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, CACHE_FILE)
        return True
    finally:
        _refreshing.release()


def refresh_in_background(on_done=None):
    def _run():
        if refresh() and on_done:
            on_done()
    threading.Thread(target=_run, daemon=True).start()


def _trip_days(get, *days):
    """{date: {'trip': name, 'note': that day's line}} for planned trips covering these days."""
    out = {}
    for trip in get('/planned-trips') or []:
        covered = [d for d in days if trip.get('start_date', '9') <= d <= trip.get('end_date', '0')]
        if not covered:
            continue
        detail = get(f"/planned-trips/{trip['id']}") or {}
        notes = {d['date']: d.get('note') for d in detail.get('days', [])}
        for d in covered:
            out[d] = {'trip': trip.get('name') or trip.get('destination') or 'Trip', 'note': notes.get(d)}
    return out


def _weather_line(cache, day):
    for w in cache.get('weather', []):
        if w.get('date') == day and w.get('temp_max') is not None:
            cond = _CONDITIONS.get(w.get('condition'), '')
            lo, hi = w.get('temp_min'), w.get('temp_max')
            temps = f"{round(lo)}–{round(hi)}°" if lo is not None else f"{round(hi)}°"
            return f"{temps} {cond}".strip()
    return ''


def _duty_line(brief):
    """'Flying · report 06:15', 'Day off · 2 of 4', or '' when there's no roster."""
    if not brief:
        return ''
    kind = brief.get('duty_type')
    label = _DUTY.get(kind, brief.get('raw_code') or '')
    if kind in ('day_off', 'vacation') and brief.get('stretch'):
        s = brief['stretch']
        return f"{label} · {s['day']} of {s['of']}"
    if brief.get('report_time'):
        return f"{label} · report {brief['report_time'][:5]}"
    return label


def _on_this_day(cache, today):
    years = ((cache.get('on_this_day') or {}).get('years') or [])
    for y in sorted(years, key=lambda e: e.get('date', ''), reverse=True):
        year = y.get('date', '')[:4]
        if not year or year == str(today.year):
            continue
        if y.get('trip_city'):
            return f"{year} · in {y['trip_city']}"
        if y.get('books'):
            return f"{year} · finished {y['books'][0].get('title', 'a book')}"
        note = (y.get('notes') or y.get('mood_note') or '').strip()
        if note:
            return f"{year} · {note.splitlines()[0]}"
    return ''


def today_view(cache, now=None):
    """Everything the Today screen draws, from the cache alone."""
    now = now or datetime.now()
    today = now.date()
    t = today.isoformat()
    fresh = cache.get('date') == t
    agenda = cache.get('agenda') or {}
    tasks = []
    if fresh:
        tasks = [('overdue', x['title']) for x in agenda.get('overdue', [])] + \
                [('today', x['title']) for x in agenda.get('today', [])]
    return {
        'weekday': now.strftime('%A'),
        'day': str(now.day),
        'month': now.strftime('%B'),
        'weather': _weather_line(cache, t) if fresh else '',
        'duty': _duty_line((cache.get('roster') or {}).get(t)) if fresh else '',
        'trip': (cache.get('trip_days') or {}).get(t) if fresh else None,
        'tasks': tasks,
        'birthdays': [b.get('name', '') for b in agenda.get('birthdays', []) if b.get('days_until') == 0] if fresh else [],
        'on_this_day': _on_this_day(cache, today) if fresh else '',
        'updated': cache.get('fetched_at', '')[11:16] if fresh else '',
        'stale': bool(cache) and not fresh,
    }


def tomorrow_view(cache, now=None):
    """What the sleep screen shows about tomorrow, or None if there's nothing worth showing."""
    now = now or datetime.now()
    tm = (now.date() + timedelta(days=1)).isoformat()
    if cache.get('date') not in (now.date().isoformat(), tm):
        return None
    duty = _duty_line((cache.get('roster') or {}).get(tm))
    trip = (cache.get('trip_days') or {}).get(tm)
    if not duty and not trip:
        return None
    d = now + timedelta(days=1)
    return {
        'label': d.strftime('%A %-d %B'),
        'duty': duty,
        'trip': trip,
        'weather': _weather_line(cache, tm),
    }
