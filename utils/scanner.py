import json
import os
from config.paths import LIBRARY_PATH


class BookInfo:
    __slots__ = ('filename', 'title', 'author')

    def __init__(self, filename, title, author):
        self.filename = filename
        self.title = title
        self.author = author


def _load_meta(stem):
    meta_path = os.path.join(LIBRARY_PATH, stem + '.meta.json')
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('title', stem), data.get('author', '')
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback: clean the stem into a readable title
        import re
        title = re.sub(r'[_\-]+', ' ', stem).strip().title()
        return title, ''


def get_books_list():
    """Return list of BookInfo objects for all books in library/, sorted by filename."""
    try:
        filenames = sorted(f for f in os.listdir(LIBRARY_PATH)
                           if f.endswith('.txt') and not f.startswith('.'))
    except FileNotFoundError:
        return []

    books = []
    for filename in filenames:
        stem = os.path.splitext(filename)[0]
        title, author = _load_meta(stem)
        books.append(BookInfo(filename, title, author))
    return books
