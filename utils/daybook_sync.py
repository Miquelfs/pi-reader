"""
Fire-and-forget sync to Daybook API (http://100.67.252.76:8000).
All calls run in daemon threads — never blocks the UI.
Failures are logged to stdout; the device works fully offline.
"""
import json
import threading
from datetime import date
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode


def _get_base_url():
    try:
        from utils.config_manager import get
        return get('daybook_url', 'http://100.67.252.76:8000').rstrip('/')
    except Exception:
        return 'http://100.67.252.76:8000'


def _post(path, payload, timeout=4):
    url = _get_base_url() + path
    data = json.dumps(payload).encode('utf-8')
    req = Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except URLError as e:
        print(f"[daybook] POST {path} failed: {e}")
        return None


def _get(path, params=None, timeout=4):
    url = _get_base_url() + path
    if params:
        url += '?' + urlencode(params)
    req = Request(url, method='GET')
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except URLError as e:
        print(f"[daybook] GET {path} failed: {e}")
        return None


def _find_book_id(title):
    """Return the Daybook book id for a given title, or None."""
    books = _get('/books')
    if not books:
        return None
    title_lower = title.lower()
    for book in books:
        if book.get('title', '').lower() == title_lower:
            return book['id']
    return None


def sync_book(title, author='', pages=None, date_finished=None, notes=''):
    """Push a book record to Daybook. Runs in a background thread."""
    def _run():
        payload = {'title': title, 'author': author, 'ownership': 'own'}
        if pages:
            payload['pages'] = pages
        if date_finished:
            payload['date_finished'] = date_finished
        if notes:
            payload['notes'] = notes
        result = _post('/books', payload)
        if result:
            print(f"[daybook] Synced book: {title!r} (id={result.get('id')})")
        else:
            print(f"[daybook] Book sync failed for {title!r}")

    threading.Thread(target=_run, daemon=True).start()


def sync_stats(streak, pages, words, hours, avg_spp, rsvp_words, rsvp_pct):
    """Push reading stats to Daybook as a note on today's day entry. Background thread."""
    def _run():
        today = date.today().isoformat()
        note = (
            f"Pi Reader stats ({today}): "
            f"{streak} day streak, "
            f"{pages:,} pages, "
            f"{words:,} words, "
            f"{hours:.1f} h reading, "
            f"{avg_spp:.0f} s/page avg, "
            f"{rsvp_words:,} RSVP words ({rsvp_pct:.0f}% of time)"
        )
        result = _post(f'/days/{today}', {'notes': note})
        if result:
            print(f"[daybook] Stats synced for {today}")
        else:
            print(f"[daybook] Stats sync failed for {today}")
    threading.Thread(target=_run, daemon=True).start()


def push_highlight(book_title, page_num, text, date_str=None):
    """Push a highlight to Daybook's book_highlights table. Runs in background."""
    if not date_str:
        date_str = date.today().isoformat()

    def _run():
        book_id = _find_book_id(book_title)
        if book_id is None:
            # Book not in Daybook yet — create it first, then push highlight
            result = _post('/books', {'title': book_title, 'ownership': 'own'})
            if result:
                book_id = result.get('id')
        if book_id is None:
            print(f"[daybook] Cannot push highlight: book {book_title!r} not found/created")
            return
        payload = {'page': page_num + 1, 'quote': text, 'date': date_str}
        result = _post(f'/books/{book_id}/highlights', payload)
        if result:
            print(f"[daybook] Highlight synced for {book_title!r} p.{page_num + 1}")
        else:
            print(f"[daybook] Highlight sync failed for {book_title!r}")

    threading.Thread(target=_run, daemon=True).start()
