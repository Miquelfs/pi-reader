"""
Turn a web page or pasted text into a library book (.txt + .meta.json).
Extraction is deliberately simple and stdlib-only: headings and paragraphs from <article>
(or <main>, or the whole page), skipping navigation, scripts and very short fragments.
"""
import json
import os
import re
from datetime import date
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from config.paths import LIBRARY_PATH

_BLOCKS = {'p', 'h1', 'h2', 'h3', 'h4', 'li', 'blockquote', 'pre'}
_SKIP = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'noscript', 'svg', 'figure', 'button'}
_MIN_PARAGRAPH = 40


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ''
        self.blocks = {'article': [], 'main': [], 'body': []}
        self._in_title = False
        self._skip = 0
        self._scope = []           # open article/main tags
        self._block = None         # (tag, [text])

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP:
            self._skip += 1
        elif tag == 'title':
            self._in_title = True
        elif tag in ('article', 'main'):
            self._scope.append(tag)
        elif tag in _BLOCKS and not self._skip:
            self._flush()
            self._block = (tag, [])
        elif tag == 'br' and self._block:
            self._block[1].append(' ')

    def handle_endtag(self, tag):
        if tag in _SKIP:
            self._skip = max(0, self._skip - 1)
        elif tag == 'title':
            self._in_title = False
        elif tag in ('article', 'main'):
            self._flush()
            if tag in self._scope:
                self._scope.remove(tag)
        elif tag in _BLOCKS:
            self._flush()

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._block and not self._skip:
            self._block[1].append(data)

    def _flush(self):
        if not self._block:
            return
        tag, parts = self._block
        self._block = None
        text = re.sub(r'\s+', ' ', ''.join(parts)).strip()
        if not text:
            return
        is_heading = tag in ('h1', 'h2', 'h3', 'h4')
        if not is_heading and len(text) < _MIN_PARAGRAPH and tag != 'li':
            return
        entry = (text.upper() if is_heading else text)
        for scope in set(self._scope) | {'body'}:
            self.blocks[scope].append(entry)


def extract(html):
    """(title, text) from an HTML page. Paragraphs are separated by blank lines;
    headings come out in capitals so the reader's parser treats them as headings."""
    p = _Extractor()
    p.feed(html)
    p.close()
    p._flush()
    body = p.blocks['article'] or p.blocks['main'] or p.blocks['body']
    title = re.sub(r'\s+', ' ', p.title).strip()
    return title, '\n\n'.join(body)


def fetch(url, timeout=20):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (pi-reader)'})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read(5_000_000)
        charset = resp.headers.get_content_charset() or 'utf-8'
    return raw.decode(charset, errors='replace')


def _slug(title):
    s = re.sub(r'[^\w\s-]', '', title, flags=re.UNICODE).strip().lower()
    return re.sub(r'[\s_-]+', '_', s)[:60] or 'article'


def save_to_library(title, text, author=''):
    """Write the book into the library; returns its filename. Never overwrites an existing book."""
    title = title.strip() or 'Untitled'
    stem = _slug(title)
    n = 2
    while os.path.exists(os.path.join(LIBRARY_PATH, stem + '.txt')):
        stem = f"{_slug(title)}_{n}"
        n += 1
    with open(os.path.join(LIBRARY_PATH, stem + '.txt'), 'w', encoding='utf-8') as f:
        f.write(text)
    meta = {'title': title, 'author': author, 'word_count': len(text.split()),
            'converted_at': date.today().isoformat()}
    with open(os.path.join(LIBRARY_PATH, stem + '.meta.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return stem + '.txt'
